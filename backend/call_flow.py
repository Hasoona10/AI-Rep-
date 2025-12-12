"""
Call flow management and conversation state handling.

This module manages the conversation flow - keeping track of what was said,
what the customer ordered, and generating appropriate responses. It also handles
order parsing from natural language (like "2 chicken shawarma wraps").
"""
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import json

from .utils.logger import logger
from .intents import Intent, classify_intent
from .rag import get_rag_system, load_business_data

# Load business data once for fast, no-LLM answers
BUSINESS_DATA_PATH = Path(__file__).parent / "business_data.json"
try:
    BUSINESS_DATA = load_business_data(BUSINESS_DATA_PATH)
except Exception as e:
    logger.error(f"Failed to load business data for fast answers: {e}")
    BUSINESS_DATA = {}

# Load follow-up question mappings for cost optimization
FOLLOWUP_MAPPINGS_PATH = Path(__file__).parent.parent / "backend" / "data" / "training" / "order_followup_mappings.json"
FOLLOWUP_MAPPINGS = {}
try:
    if FOLLOWUP_MAPPINGS_PATH.exists():
        with open(FOLLOWUP_MAPPINGS_PATH, 'r', encoding='utf-8') as f:
            FOLLOWUP_MAPPINGS = json.load(f)
        logger.info(f"Loaded {len(FOLLOWUP_MAPPINGS)} follow-up question mappings for cost optimization")
    else:
        logger.info("Follow-up mappings file not found, continuing without it")
except Exception as e:
    logger.warning(f"Failed to load follow-up mappings: {e}")


class ConversationState:
    """
    Manages conversation state for a call.
    
    This keeps track of everything that happens in a conversation - the messages,
    the current intent, any orders being placed, etc. It's basically the memory
    for each phone call or chat session.
    """
    
    def __init__(self, call_sid: str, business_id: str = "restaurant_001"):
        """
        Initialize conversation state.
        
        Each call/chat gets its own ConversationState object to track what's happening.
        I'm storing order items in a simple list format (like a POS system).
        
        Args:
            call_sid: Twilio Call SID (unique ID for each call)
            business_id: Business identifier (defaults to restaurant_001)
        """
        self.call_sid = call_sid
        self.business_id = business_id
        self.messages: List[Dict] = []
        self.current_intent: Optional[Intent] = None
        self.reservation_context: Optional[Dict] = None
        # Simple POS-style order state for this call
        # Each item: {"name": str, "quantity": int, "unit_price": float, "total_price": float}
        self.order_items: List[Dict] = []
        # Optional finalized ticket for kitchen view when order is closed
        # {"items": [...], "total": float, "note": str}
        self.kitchen_ticket: Optional[Dict] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert conversation state to dictionary."""
        return {
            "call_sid": self.call_sid,
            "business_id": self.business_id,
            "messages": self.messages,
            "current_intent": self.current_intent.value if self.current_intent else None,
            "reservation_context": self.reservation_context,
            "order_items": self.order_items,
            "kitchen_ticket": self.kitchen_ticket,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


# In-memory conversation storage (use Redis/database in production)
conversations: Dict[str, ConversationState] = {}

# Simple orders log file for demo / owner view
ORDERS_LOG_PATH = Path(__file__).parent / "orders_log.json"


def log_order(
    call_sid: str,
    business_id: str,
    customer_text: str,
    ai_response: str,
    intent: Optional[Intent] = None,
    conversation: Optional[ConversationState] = None,
    response_source: Optional[str] = None,
) -> None:
    """
    Append a structured order-like record to orders_log.json.

    We now log both the raw utterance + AI response and the
    structured order snapshot (items + totals) so the owner
    can see exactly what was ordered.
    """
    try:
        record: Dict[str, object] = {
            "timestamp": datetime.utcnow().isoformat(),
            "call_sid": call_sid,
            "business_id": business_id,
            "intent": intent.value if intent else None,
            "customer_text": customer_text,
            "ai_response": ai_response,
            "response_source": response_source or "unknown",  # Track: template, LLM, cached, etc.
        }

        # Optionally include a small conversation snapshot and order snapshot
        if conversation is not None:
            # Last few messages only, to keep things readable
            record["conversation_tail"] = conversation.messages[-6:]
            # POS-style order snapshot for this call
            if conversation.order_items:
                record["order_items"] = conversation.order_items
                total = 0.0
                for item in conversation.order_items:
                    total += float(item.get("total_price", 0.0))
                record["order_total"] = total
            # Finalized kitchen ticket snapshot (if available)
            if conversation.kitchen_ticket:
                record["kitchen_ticket"] = conversation.kitchen_ticket

        if ORDERS_LOG_PATH.exists():
            with ORDERS_LOG_PATH.open("r", encoding="utf-8") as f:
                existing = json.load(f)
            if not isinstance(existing, list):
                existing = []
        else:
            existing = []

        existing.append(record)

        with ORDERS_LOG_PATH.open("w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)

        logger.info(f"Logged potential order for call {call_sid}")
    except Exception as e:
        logger.error(f"Error logging order for call {call_sid}: {str(e)}")


def answer_from_facts(text: str) -> Optional[str]:
    """
    Try to answer common questions directly from business_data.json
    without calling the LLM. This keeps the agent fast and robust.
    """
    if not BUSINESS_DATA:
        return None

    q = text.lower()

    # Hours
    if any(k in q for k in ["hour", "open", "close", "time"]):
        hours = BUSINESS_DATA.get("hours", {})
        if hours:
            parts = [f"{day.capitalize()}: {val}" for day, val in sorted(hours.items())]
            return "Our hours are: " + "; ".join(parts)

    # Halal
    if "halal" in q:
        if BUSINESS_DATA.get("services", {}).get("halal_meat"):
            return (
                "Yes, we serve halal meat at Cedar Garden Lebanese Kitchen. "
                "If you have any specific questions or allergies, we're happy to help."
            )

    # Vegetarian / vegan
    if "vegetarian" in q or "vegan" in q:
        for f in BUSINESS_DATA.get("faq", []):
            tags = " ".join(f.get("tags", [])).lower()
            if "vegetarian" in tags or "vegan" in tags:
                return f.get("answer")

    # Gluten-free
    if "gluten" in q:
        for f in BUSINESS_DATA.get("faq", []):
            tags = " ".join(f.get("tags", [])).lower()
            if "gluten_free" in tags:
                return f.get("answer")

    # Parking / location
    if "parking" in q or "park" in q:
        loc = BUSINESS_DATA.get("location_info", {})
        if "parking" in loc:
            return loc["parking"]

    # Catering / trays / party
    if any(k in q for k in ["cater", "catering", "party", "tray"]):
        for f in BUSINESS_DATA.get("faq", []):
            tags = " ".join(f.get("tags", [])).lower()
            if "catering" in tags:
                return f.get("answer")

    # Menu questions - popular items
    if any(k in q for k in ["popular", "best", "recommend", "favorite", "favourite", "what's good"]):
        popular_items = []
        for section in BUSINESS_DATA.get("menu_sections", []):
            for item in section.get("items", []):
                if item.get("popular"):
                    name = item.get("name", "")
                    price = item.get("price", 0)
                    if isinstance(price, (int, float)):
                        price_str = f"${price:.2f}"
                    else:
                        price_str = str(price)
                    popular_items.append(f"{name} - {price_str}")
        
        if popular_items:
            items_text = ", ".join(popular_items[:5])  # Top 5 popular items
            return (
                f"Our most popular items are: {items_text}. "
                "Would you like to know more about any of these or place an order?"
            )

    # Menu questions - what's on the menu / what do you have
    if any(k in q for k in ["what's on the menu", "what do you have", "what do you serve", "menu", "what can i get"]):
        menu_sections = BUSINESS_DATA.get("menu_sections", [])
        section_names = [s.get("name", "") for s in menu_sections[:5]]  # Top 5 sections
        sections_text = ", ".join(section_names)
        return (
            f"We have a variety of Lebanese dishes including: {sections_text}. "
            "Would you like to hear about specific items or place an order?"
        )

    # Sandwich/wrap questions
    if any(k in q for k in ["sandwich", "sandwiches", "wrap", "wraps"]):
        wraps_section = None
        for section in BUSINESS_DATA.get("menu_sections", []):
            if "wrap" in section.get("name", "").lower() or "sandwich" in section.get("name", "").lower():
                wraps_section = section
                break
        
        if wraps_section:
            items = []
            for item in wraps_section.get("items", []):
                name = item.get("name", "")
                price = item.get("price", 0)
                if isinstance(price, (int, float)):
                    price_str = f"${price:.2f}"
                else:
                    price_str = str(price)
                items.append(f"{name} - {price_str}")
            
            if items:
                items_text = ", ".join(items)
                return (
                    f"Here are our wraps and sandwiches: {items_text}. "
                    "Which would you like to order?"
                )

    # Pricing questions - check for specific item mentions
    for name, item in MENU_INDEX.items():
        if name in q:
            price = item.get("price", 0)
            if isinstance(price, (int, float)):
                price_str = f"${price:.2f}"
            else:
                price_str = str(price)
            description = item.get("description", "")
            return (
                f"{item.get('name')} costs {price_str}. "
                f"{description} Would you like to add this to your order?"
            )

    # Location/address questions (but NOT unrelated questions that happen to contain "where")
    # Check for unrelated keywords first to avoid false matches
    unrelated_in_q = any(kw in q for kw in ["weather", "temperature", "news", "sports", "movie", "joke"])
    if not unrelated_in_q and any(k in q for k in ["where", "location", "address", "located"]):
        address = BUSINESS_DATA.get("address", {})
        if isinstance(address, dict):
            street = address.get("street", "")
            city = address.get("city", "")
            state = address.get("state", "")
            zip_code = address.get("zip", "")
            location_text = (
                f"We're located at {street}, {city}, {state} {zip_code}. "
                "We're in Cedar Grove Plaza near the intersection of Chapman Ave and State College Blvd."
            )
            # If user also asks about timing ("when will the order be ready"), include that
            if any(k in q for k in ["when", "ready", "time", "pickup", "how long"]):
                return f"{location_text} Your order will be ready for pickup in approximately 25-30 minutes."
            return location_text

    # Main dish customization questions
    if any(k in q for k in ["shawarma", "shawarmas"]):
        if any(k in q for k in ["bread", "pita", "markouk", "wrap"]):
            return (
                "Our shawarma comes on warm Lebanese pita bread. "
                "Would you like any additions like pickles, garlic sauce, or tahini?"
            )
        if "spicy" in q or "extra spice" in q:
            return "I can add extra spice to your shawarma. Would you like mild, medium, or extra spicy?"
    
    if "mixed grill" in q:
        if "large" in q or "extra" in q:
            return (
                "Our mixed grill comes with chicken kabob, beef kabob, and kafta skewers, "
                "served with rice, grilled vegetables, and garlic sauce. "
                "Would you like any extra skewers added?"
            )
        return (
            "Our mixed grill includes chicken kabob, beef kabob, and kafta, "
            "served with rice, grilled vegetables, and garlic sauce. "
            "Would you like to order this?"
        )
    
    if "kibbeh" in q:
        if "spicy" in q or "extra spice" in q:
            return "I can make your kibbeh extra spicy. Would you like to add that to your order?"
        return "Our kibbeh is a traditional Lebanese dish. Would you like the fried or raw version?"
    
    if "kafta" in q or "lamb kafta" in q:
        return (
            "Our kafta comes with your choice of two sides: rice, grilled vegetables, "
            "tabbouleh, or fattoush salad. Which would you like?"
        )
    
    if "vegetarian platter" in q or "vegetarian plate" in q:
        return (
            "Our vegetarian platter includes hummus, baba ghanoush, tabbouleh, fattoush, "
            "and falafel. Which dip would you prefer as the main feature: hummus or baba ghanoush?"
        )
    
    if "garlic sauce" in q or "toum" in q or "extra garlic" in q:
        return "I can add extra garlic sauce (toum) to your order for $1.00. Would you like that?"
    
    if "falafel" in q and ("sandwich" in q or "wrap" in q or "4" in q or "four" in q):
        return (
            "Our falafel is available as a wrap, in pita, or as a platter. "
            "Which would you prefer?"
        )
    
    if "manakish" in q or ("shawarma" in q and "manakish" in q):
        return (
            "Shawarma is a meat wrap with marinated chicken or beef. "
            "Manakish is a flatbread with toppings like za'atar, cheese, or ground meat. "
            "Which would you like?"
        )
    
    if "whole fish" in q or "roasted fish" in q:
        return (
            "We offer whole roasted fish. Please call ahead to check today's availability. "
            "Would you like to place an order?"
        )

    # Appetizers, sides, and mezze questions
    if "mezze" in q or "sampler" in q:
        if "small" in q:
            return (
                "Our small mezze sampler includes hummus, baba ghanoush, tabbouleh, and grape leaves. "
                "Would you like the full size sampler instead? It includes more items."
            )
        return (
            "Our mezze sampler includes hummus, baba ghanoush, tabbouleh, fattoush, "
            "grape leaves, and falafel. Would you like to order this?"
        )
    
    if "hummus" in q and ("price" in q or "cost" in q or "how much" in q):
        hummus_item = MENU_INDEX.get("hummus")
        if hummus_item:
            price = hummus_item.get("price", 0)
            if isinstance(price, (int, float)):
                return f"A standard order of hummus is ${price:.2f}."
        return "A standard order of hummus is $9.50."
    
    if "baba ghanoush" in q or "baba ghanouj" in q:
        if "smoky" in q:
            return "Yes, we roast the eggplant over an open flame for a distinct smoky flavor."
        baba_item = MENU_INDEX.get("baba ghanoush")
        if baba_item:
            price = baba_item.get("price", 0)
            if isinstance(price, (int, float)):
                return f"Baba Ghanoush is ${price:.2f}."
        return "Baba Ghanoush is $10.00."
    
    if "grape leaves" in q or "warak" in q:
        if "two" in q or "2" in q:
            return (
                "We have both meat-filled and vegetarian grape leaves. "
                "Which would you prefer?"
            )
        return "We offer grape leaves (warak enab) - would you like the vegetarian or meat-filled version?"
    
    if "dips" in q and ("besides" in q or "other" in q or "what" in q):
        dips = ["Hummus", "Baba Ghanoush", "Labneh", "Moutabbal"]
        return f"We offer: {', '.join(dips)}. Which would you like?"
    
    if "pita" in q and ("extra" in q or "more" in q):
        return "Yes, an extra basket of pita bread is $2.00. Would you like to add that?"
    
    if "fattoush" in q and ("dressing" in q or "what's in" in q):
        return "Our fattoush dressing is made with sumac, olive oil, lemon juice, and mint."
    
    if "kibbeh nayyeh" in q or "raw kibbeh" in q:
        return (
            "Kibbeh Nayyeh is raw meat, best consumed immediately. "
            "We adhere to strict preparation standards. Would you like to order this?"
        )
    
    if "pickles" in q and "turnips" in q:
        return "I can add pickles and turnips as a side. Would you like that?"

    # Dessert questions
    if "knafeh" in q:
        knafeh_item = MENU_INDEX.get("knafeh")
        if knafeh_item:
            price = knafeh_item.get("price", 0)
            if isinstance(price, (int, float)):
                return f"Yes, our Knafeh is made fresh daily and costs ${price:.2f}."
        return "Yes, our Knafeh is made fresh daily and costs $9.50."
    
    if "dessert" in q and ("options" in q or "what" in q):
        desserts = []
        for section in BUSINESS_DATA.get("menu_sections", []):
            if "dessert" in section.get("name", "").lower():
                for item in section.get("items", []):
                    name = item.get("name", "")
                    desserts.append(name)
        if desserts:
            return f"We offer: {', '.join(desserts)}. Which would you like?"
        return "We offer Baklava, Knafeh, and Rice Pudding. Which would you like?"
    
    if "turkish coffee" in q or "lebanese coffee" in q:
        if "strong" in q:
            return "Our Lebanese coffee is traditionally strong, made with finely ground beans and cardamom."
        return (
            "Would you like your Turkish coffee plain, medium sweet, or very sweet? "
            "We also add cardamom for traditional flavor."
        )
    
    if "baklava" in q:
        if "sampler" in q:
            return (
                "Our baklava sampler includes walnut, pistachio, and mixed varieties for $10.00. "
                "Would you like to order this?"
            )
        if "4" in q or "four" in q or "pieces" in q:
            return "Which baklava varieties would you like: Walnut, Pistachio, or Mixed?"
        baklava_item = MENU_INDEX.get("baklava")
        if baklava_item:
            price = baklava_item.get("price", 0)
            if isinstance(price, (int, float)):
                return f"Baklava is ${price:.2f} per piece."
        return "Baklava is $8.50 per piece."
    
    if "mint tea" in q:
        return "Would you prefer fresh mint tea or a teabag? We recommend fresh mint for the best flavor."
    
    if "mohallabieh" in q or "muhallabieh" in q:
        if "dairy" in q or "dairy-free" in q:
            return "No, Mohallabieh is a milk pudding, so it contains dairy."
        return "Mohallabieh is a traditional milk pudding. Would you like to order it?"
    
    if "ice cream" in q:
        return "Yes, we offer rosewater and pistachio ice cream. Which would you like?"
    
    if "knafeh" in q and "syrup" in q:
        return "The syrup on knafeh is a light rosewater and orange blossom simple syrup (atter)."

    # Drink questions
    if "fresh juice" in q or "juice" in q:
        return (
            "Our fresh juices today include: Mint Lemonade, Carrot Juice, and Orange Juice. "
            "Which would you like?"
        )
    
    if "lemonade" in q:
        if "pitcher" in q:
            return "Would you like the lemonade plain or with rosewater or mint added?"
        lemonade_item = MENU_INDEX.get("mint lemonade")
        if lemonade_item:
            price = lemonade_item.get("price", 0)
            if isinstance(price, (int, float)):
                return f"Mint Lemonade is ${price:.2f}."
        return "Mint Lemonade is $5.50."
    
    if "coke" in q or "coca cola" in q:
        if "how much" in q or "price" in q or "cost" in q:
            soft_drinks = MENU_INDEX.get("soft drinks")
            if soft_drinks:
                price = soft_drinks.get("price", 0)
                if isinstance(price, (int, float)):
                    return f"A can of Coke is ${price:.2f}."
            return "A can of Coke is $3.50."
        return "Yes, we have Coke and other soft drinks. Would you like to add one to your order?"
    
    if "lemonade" in q and ("honey" in q or "sweetened" in q):
        return "Our lemonade is sweetened with simple sugar, not honey."

    # Delivery and catering questions
    if "cater" in q or "catering" in q:
        if "events" in q or "event" in q:
            return (
                "Yes, we offer catering for events up to 100 people. "
                "Our catering menu includes mezze trays, mixed grill trays, and family meals. "
                "Would you like more details?"
            )
        return "Yes, we offer catering. For large orders, we typically need 24-48 hours notice."
    
    if "delivery" in q:
        if "how long" in q or "when" in q or "time" in q:
            return "Your estimated delivery time is 30-40 minutes."
        if "minimum" in q:
            return "The minimum order for delivery is $20.00."
        if "third-party" in q or "doordash" in q or "uber" in q:
            delivery_partners = BUSINESS_DATA.get("services", {}).get("delivery_partners", [])
            if delivery_partners:
                return f"Yes, we use {', '.join(delivery_partners)} for delivery."
            return "We use our own drivers for local delivery within 5 miles."
        if "packaged" in q or "packaging" in q:
            return "All hot items are sealed in insulated containers for delivery."
    
    if "banquet" in q or ("12" in q and "people" in q):
        return (
            "Our standard banquet menu for 12 people is $35 per person. "
            "It includes a variety of mezze, mixed grill, rice, salads, and dessert. "
            "Would you like to book this?"
        )
    
    if "pickup" in q and ("tomorrow" in q or "6" in q or "6 pm" in q):
        return (
            "I can schedule your order for pickup tomorrow at 6 PM. "
            "What would you like to order?"
        )
    
    if "family meal" in q or "family feast" in q:
        return (
            "Yes, our Family Feast serves 4-5 people and includes: "
            "mixed grill, rice, hummus, baba ghanoush, tabbouleh, fattoush, and pita bread. "
            "Would you like to order this?"
        )
    
    if "cancel" in q and "order" in q:
        return (
            "I can help you cancel your order. Please provide your order number or phone number. "
            "Are you sure you'd like to cancel?"
        )
    
    if "pick up" in q and ("where" in q or "pickup" in q):
        return "Pickup is at the front counter labeled 'Online Orders'. Just let us know your name when you arrive."

    return None


def answer_from_intent(text: str, intent: Intent) -> Optional[str]:
    """
    Generate responses based on intent classification without using LLM.
    This is the cost-saving function that uses templates and business data.
    """
    if not BUSINESS_DATA:
        return None
    
    q = text.lower()
    
    # MENU intent - provide menu information
    if intent == Intent.MENU:
        # Check if asking about specific category
        if any(k in q for k in ["mezze", "appetizer", "starter"]):
            mezze_items = []
            for section in BUSINESS_DATA.get("menu_sections", []):
                if "mezze" in section.get("name", "").lower():
                    for item in section.get("items", [])[:3]:  # Top 3
                        name = item.get("name", "")
                        price = item.get("price", 0)
                        if isinstance(price, (int, float)):
                            price_str = f"${price:.2f}"
                        else:
                            price_str = str(price)
                        mezze_items.append(f"{name} - {price_str}")
            if mezze_items:
                return f"Our mezze options include: {', '.join(mezze_items)}. Would you like to order any?"
        
        # General menu question
        popular_items = []
        for section in BUSINESS_DATA.get("menu_sections", []):
            for item in section.get("items", []):
                if item.get("popular"):
                    name = item.get("name", "")
                    price = item.get("price", 0)
                    if isinstance(price, (int, float)):
                        price_str = f"${price:.2f}"
                    else:
                        price_str = str(price)
                    popular_items.append(f"{name} - {price_str}")
                    if len(popular_items) >= 5:
                        break
            if len(popular_items) >= 5:
                break
        
        if popular_items:
            items_text = ", ".join(popular_items)
            return (
                f"Here are some of our popular items: {items_text}. "
                "What would you like to order?"
            )
        
        # Fallback: list menu sections
        menu_sections = BUSINESS_DATA.get("menu_sections", [])
        section_names = [s.get("name", "") for s in menu_sections[:4]]
        return f"We offer: {', '.join(section_names)}. What interests you?"
    
    # PRICING intent - provide pricing information
    elif intent == Intent.PRICING:
        # Try to find specific item mentioned
        for name, item in MENU_INDEX.items():
            if name in q:
                price = item.get("price", 0)
                if isinstance(price, (int, float)):
                    price_str = f"${price:.2f}"
                else:
                    price_str = str(price)
                return f"{item.get('name')} is {price_str}. Would you like to add it to your order?"
        
        # General pricing question
        return (
            "Our prices range from $9.50 for mezze items to $28 for entrees. "
            "Wraps and sandwiches are around $14-$16. Would you like to know the price of a specific item?"
        )
    
    # HOURS intent - already handled in answer_from_facts, but double-check
    elif intent == Intent.HOURS:
        hours = BUSINESS_DATA.get("hours", {})
        if hours:
            parts = [f"{day.capitalize()}: {val}" for day, val in sorted(hours.items())]
            return "Our hours are: " + "; ".join(parts)
    
    # DIRECTION intent - location information
    # BUT: Don't return location if question is clearly unrelated (weather, news, etc.)
    # OR if user said something very short (likely a confirmation, not a location question)
    elif intent == Intent.DIRECTION:
        # Check if this is actually an unrelated question that was misclassified
        unrelated_in_q = any(kw in q for kw in ["weather", "temperature", "news", "sports", "movie", "joke", "forecast"])
        if unrelated_in_q:
            return None  # Let the unrelated question handler catch it
        
        # If user said something very short (1-3 words) and it's not explicitly asking about location,
        # don't return location - it's likely a misclassified confirmation
        if len(q.split()) <= 3 and not any(k in q for k in ["where", "location", "address", "directions", "find", "map"]):
            return None
        
        address = BUSINESS_DATA.get("address", {})
        if isinstance(address, dict):
            street = address.get("street", "")
            city = address.get("city", "")
            state = address.get("state", "")
            zip_code = address.get("zip", "")
            location_info = BUSINESS_DATA.get("location_info", {})
            landmarks = location_info.get("landmarks", "")
            return (
                f"We're located at {street}, {city}, {state} {zip_code}. "
                f"{landmarks} Would you like directions?"
            )
    
    # RESERVATION intent - provide reservation info
    elif intent == Intent.RESERVATION:
        reservation_rules = BUSINESS_DATA.get("reservation_rules", {})
        phone = BUSINESS_DATA.get("contact", {}).get("phone", "(714) 555-8734")
        return (
            f"Yes, we take reservations! You can call us at {phone}. "
            "We accept reservations for parties of 1 to 10 guests. "
            "For larger parties, please call ahead. Would you like to make a reservation?"
        )
    
    return None


def _build_menu_index() -> Dict[str, Dict]:
    """
    Build a simple lookup from lowercase item name to menu item data.
    """
    index: Dict[str, Dict] = {}
    for section in BUSINESS_DATA.get("menu_sections", []):
        for item in section.get("items", []):
            name = item.get("name")
            if not name:
                continue
            index[name.lower()] = item
    return index


MENU_INDEX = _build_menu_index()


def _parse_quantity_and_item(text: str) -> Optional[Dict]:
    """
    Very simple parser to pull out quantity and an item name present in the menu.
    Examples it should catch:
      - \"2 chicken shawarma wraps\"
      - \"two chicken shawarma sandwiches\" (will treat as quantity 2 if digit present)
    """
    import re

    q = text.lower()

    # Normalize common ASR mis-hearings for shawarma / sandwiches
    replacements = {
        "shore my": "shawarma",
        "shorma": "shawarma",
        "shwarma": "shawarma",
        "sandwhich": "sandwich",
        "sandwhiches": "sandwiches",
        "sandwhichs": "sandwiches",
        "fattouch": "fattoush",
        "fatoush": "fattoush",
    }
    for wrong, right in replacements.items():
        q = q.replace(wrong, right)

    # 1) Quantity: prefer explicit digit, then small number words
    qty_match = re.search(r"(?:^|\s)(\d+)(?:\s+)", q)
    if qty_match:
        quantity = int(qty_match.group(1))
    else:
        number_words = {
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
            "ten": 10,
        }
        quantity = 1
        for word, val in number_words.items():
            if re.search(rf"\b{word}\b", q):
                quantity = val
                break

    # 2) Find the best matching menu item name that appears in the text
    matched_name = None
    best_score = 0

    # If caller says "wrap" or "sandwich", prefer wrap/sandwich items first
    prefers_wrap = "wrap" in q or "sandwich" in q

    for name, item in MENU_INDEX.items():
        lname = name.lower()
        core = lname.replace("wrap", "").replace("sandwich", "").strip()
        if not core:
            continue

        # Filter to wrap/sandwich items when appropriate
        if prefers_wrap and ("wrap" not in lname and "sandwich" not in lname):
            continue

        if core in q:
            score = len(core)
            if score > best_score:
                best_score = score
                matched_name = name

    # If we filtered to wraps and found nothing, fall back to any item
    if not matched_name:
        for name, item in MENU_INDEX.items():
            lname = name.lower()
            core = lname.replace("wrap", "").replace("sandwich", "").strip()
            if not core:
                continue
            if core in q:
                score = len(core)
                if score > best_score:
                    best_score = score
                    matched_name = name

    if not matched_name:
        return None

    item = MENU_INDEX[matched_name]
    unit_price = float(item.get("price", 0.0))

    return {
        "name": item.get("name"),
        "quantity": quantity,
        "unit_price": unit_price,
        "total_price": unit_price * quantity,
    }


def _parse_multiple_items(text: str) -> List[Dict]:
    """
    Parse multiple items from a single message.
    Handles complex orders like: "3 shawarma sandwiches, 1 beef and 2 chicken, 1 hummus plate, 1 fattoush salad"
    """
    import re
    
    items = []
    q = text.lower()
    
    # Normalize common ASR mis-hearings and aliases
    replacements = {
        "shore my": "shawarma",
        "shorma": "shawarma",
        "shwarma": "shawarma",
        "sandwhich": "sandwich",
        "sandwhiches": "sandwiches",
        "sandwhichs": "sandwiches",
    }
    for wrong, right in replacements.items():
        q = q.replace(wrong, right)
    
    # Handle aliases for menu items (check both singular and plural)
    item_aliases = {
        "coke": "soft drinks",
        "cokes": "soft drinks",  # Plural
        "coca cola": "soft drinks",
        "soda": "soft drinks",
        "sodas": "soft drinks",  # Plural
        "soft drink": "soft drinks",
        "soft drinks": "soft drinks",
        "fries": "french fries",
        "french fries": "french fries",
        "side of fries": "french fries",
        "sides of fries": "french fries",  # Plural
        "fattouch": "fattoush",
        "fatoush": "fattoush",
        "fattouch salad": "fattoush",
        "fatoush salad": "fattoush",
        "laban-up": "laban",
        "laban up": "laban",
        "labneh": "labneh",
        "labne": "labneh",
        "shawarma": "chicken shawarma wrap",  # Default to chicken when just "shawarma"
        "shawarmas": "chicken shawarma wrap",  # Plural
        "beef shawarma": "beef shawarma wrap",
        "beef shawarmas": "beef shawarma wrap",  # Plural
        "chicken shawarma": "chicken shawarma wrap",
        "chicken shawarmas": "chicken shawarma wrap",  # Plural
        "shawarma sandwich": "chicken shawarma wrap",  # Default to chicken
        "chicken shawarma sandwich": "chicken shawarma wrap",
        "beef shawarma sandwich": "beef shawarma wrap",
        "lamb skewer": "beef kabob plate",  # Closest match
        "shish taouk": "chicken kabob plate",
        "shish taouk plate": "chicken kabob plate",
        "house burger": "kafta wrap",  # Kafta-based burger
        "vegetarian platter": "mezze party tray",  # Closest match
        "za'atar manakish": "manakish",
        "zaatar manakish": "manakish",
        "kibbeh nayyeh": "fried kibbeh",  # Closest match
        "mint lemonade": "lemonade",
        "turkish coffee": "lebanese coffee",  # Closest match
    }

    # Extras not present in menu (fallback items)
    extra_items = {
        "french fries": {"name": "French Fries", "price": 5.00},
        "fries": {"name": "French Fries", "price": 5.00},
    }
    
    # Split by common separators: comma, "and", "&"
    # Pattern: number + item description
    # Examples: "3 shawarma", "1 beef and 2 chicken", "1 hummus plate"
    
    # First, handle complex cases like "1 beef and 2 chicken shawarma"
    # Pattern: (\d+)\s+(\w+)\s+and\s+(\d+)\s+(\w+)\s+(shawarma|wrap|sandwich)
    complex_pattern = r"(\d+)\s+(\w+)\s+and\s+(\d+)\s+(\w+)\s+(shawarma|wrap|sandwich|sandwiches)"
    complex_matches = re.finditer(complex_pattern, q)
    for match in complex_matches:
        qty1, type1, qty2, type2, item_type = match.groups()
        # Try to match "beef shawarma" and "chicken shawarma"
        for name, item in MENU_INDEX.items():
            lname = name.lower()
            if type1 in lname and item_type in lname:
                items.append({
                    "name": item.get("name"),
                    "quantity": int(qty1),
                    "unit_price": float(item.get("price", 0.0)),
                    "total_price": float(item.get("price", 0.0)) * int(qty1),
                })
            if type2 in lname and item_type in lname:
                items.append({
                    "name": item.get("name"),
                    "quantity": int(qty2),
                    "unit_price": float(item.get("price", 0.0)),
                    "total_price": float(item.get("price", 0.0)) * int(qty2),
                })
        # Remove this from text to avoid double parsing
        q = q.replace(match.group(0), "")
    
    # Now parse simple patterns: split by comma or "and" 
    # Better approach: split the text into segments first
    segments = re.split(r',\s*|\s+and\s+', q)
    
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        
        # Match: number + item description (number might not be at start)
        # Handle patterns like: "3 beef shawarma", "add 3 cokes", "i would like 3 beef shawarma"
        match = re.search(r"(\d+)\s+(.+)", segment)
        if not match:
            continue
        
        qty_str, item_desc = match.groups()
        quantity = int(qty_str)
        item_desc = item_desc.strip().lower()
        
        # Skip if we already parsed this in complex pattern (check for processed markers)
        if segment.startswith("__processed"):
            continue
        
        # Apply aliases to item description (check whole words to avoid partial matches)
        # IMPORTANT: Apply aliases BEFORE matching to menu items
        for alias, menu_name in item_aliases.items():
            # Use word boundaries to match whole words
            alias_pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(alias_pattern, item_desc):
                item_desc = re.sub(alias_pattern, menu_name, item_desc)
                logger.info(f"✅ Applied alias: '{alias}' → '{menu_name}' for item description")
        
        # Remove common words that don't help matching but keep key identifiers
        # Don't remove "wrap" or "sandwich" if they're part of the item name (like "shawarma wrap")
        item_desc_clean = item_desc
        # Only remove these if they're standalone (not part of a compound name)
        if "shawarma" not in item_desc and "wrap" not in item_desc:
            item_desc_clean = re.sub(r'\b(plate|sandwich|sandwiches|wrap|wraps)\b', '', item_desc).strip()
        if not item_desc_clean:
            item_desc_clean = item_desc  # Keep original if cleaning removed everything
        
        # Try to match item description to menu items
        matched_name = None
        best_score = 0
        
        for name, item in MENU_INDEX.items():
            lname = name.lower()
            
            # Direct substring match (most reliable)
            if item_desc_clean in lname or item_desc in lname:
                score = 100
                if score > best_score:
                    best_score = score
                    matched_name = name
                continue
            
            # Special case: "beef shawarma" should match "beef shawarma wrap"
            # "chicken shawarma" should match "chicken shawarma wrap"
            if "beef shawarma" in item_desc and "beef shawarma wrap" in lname:
                score = 100
                if score > best_score:
                    best_score = score
                    matched_name = name
                continue
            if "chicken shawarma" in item_desc and "chicken shawarma wrap" in lname:
                score = 100
                if score > best_score:
                    best_score = score
                    matched_name = name
                continue
            
            # Word-based matching
            desc_words = set(item_desc.split())
            name_words = set(lname.split())
            common_words = desc_words.intersection(name_words)
            
            if len(common_words) > 0:
                score = len(common_words) * 2
                
                # Bonus for key words
                if "hummus" in item_desc and "hummus" in lname:
                    score += 10
                if "fattoush" in item_desc and "fattoush" in lname:
                    score += 10
                if "shawarma" in item_desc and "shawarma" in lname:
                    score += 5
                if "beef" in item_desc and "beef" in lname:
                    score += 3
                if "chicken" in item_desc and "chicken" in lname:
                    score += 3
                if "soft drinks" in item_desc and "soft drinks" in lname:
                    score += 10
                
                if score > best_score:
                    best_score = score
                    matched_name = name
        
        if matched_name and best_score > 0:
            item = MENU_INDEX[matched_name]
            items.append({
                "name": item.get("name"),
                "quantity": quantity,
                "unit_price": float(item.get("price", 0.0)),
                "total_price": float(item.get("price", 0.0)) * quantity,
            })
            logger.info(f"✅ Matched '{item_desc}' to '{matched_name}' with quantity {quantity}")
        else:
            # Fallback: extras not in menu (e.g., fries, soft drinks)
            # Check for soft drinks (coke, soda, etc.) first
            if any(drink_word in item_desc for drink_word in ["coke", "cokes", "soda", "sodas", "soft drink", "soft drinks"]):
                # Find soft drinks in menu
                soft_drinks_item = MENU_INDEX.get("soft drinks")
                if soft_drinks_item:
                    items.append({
                        "name": soft_drinks_item.get("name", "Soft Drinks"),
                        "quantity": quantity,  # Use the parsed quantity, not default 1
                        "unit_price": float(soft_drinks_item.get("price", 3.50)),
                        "total_price": float(soft_drinks_item.get("price", 3.50)) * quantity,
                    })
                    logger.info(f"✅ Added {quantity} Soft Drinks from fallback (coke/cokes/soda detected)")
                else:
                    # If not in menu, create it with default price
                    items.append({
                        "name": "Soft Drinks",
                        "quantity": quantity,
                        "unit_price": 3.50,
                        "total_price": 3.50 * quantity,
                    })
                    logger.info(f"✅ Added {quantity} Soft Drinks (not in menu, using default price)")
                continue  # Skip fries check if we already added soft drinks
            # Check for fries
            elif any(fries_word in item_desc for fries_word in ["fries", "french fries", "side of fries", "sides of fries"]):
                for extra_key, extra in extra_items.items():
                    if extra_key in item_desc or extra_key in item_desc_clean:
                        price = float(extra.get("price", 0.0))
                        items.append({
                            "name": extra.get("name"),
                            "quantity": quantity,
                            "unit_price": price,
                            "total_price": price * quantity,
                        })
                        break
    
    # If no items found with complex parsing, fall back to single item parser
    if not items:
        single_item = _parse_quantity_and_item(text)
        if single_item:
            items.append(single_item)
    
    return items


def _get_order_followup_question(item_name: str, conversation: ConversationState) -> Optional[str]:
    """
    Generate a follow-up question based on the item that was just ordered.
    This makes the ordering experience more interactive and helps customers customize their order.
    
    Args:
        item_name: Name of the item that was just added
        conversation: Current conversation state
        
    Returns:
        Follow-up question string, or None if no follow-up needed
    """
    item_lower = item_name.lower()
    
    # Shawarma/Sandwich customization
    if "shawarma" in item_lower or ("chicken" in item_lower and "wrap" in item_lower) or ("beef" in item_lower and "wrap" in item_lower):
        return "Would you like it with extra garlic sauce (toum) or spicy chili paste?"
    
    # Soup orders
    if "soup" in item_lower or "lentil" in item_lower:
        return "Would you like a side of pita chips with that?"
    
    # Skewer orders (a la carte)
    if "skewer" in item_lower or ("lamb" in item_lower and "skewer" in item_lower):
        return "That's a la carte. Is the skewer to be cooked medium, medium-well, or well done?"
    
    # Falafel wrap
    if "falafel" in item_lower and ("wrap" in item_lower or "sandwich" in item_lower):
        return "Is this for immediate pickup, or would you like to schedule a time?"
    
    # Vegetarian platter
    if "vegetarian platter" in item_lower or "vegetarian plate" in item_lower:
        return "Which two vegetarian pastries would you like included? We have cheese roll, spinach pie, and more."
    
    # Shish Taouk / Chicken plate
    if "shish taouk" in item_lower or ("chicken" in item_lower and "plate" in item_lower and "kabob" in item_lower):
        return "Your plate comes with rice and your choice of salad (tabbouleh, fattoush, or simple garden). Which would you prefer?"
    
    # Manakish
    if "manakish" in item_lower or "za'atar" in item_lower:
        return "Would you like any additions like tomato and mint?"
    
    # House burger / Kafta burger
    if "burger" in item_lower or ("kafta" in item_lower and "burger" in item_lower):
        return "Our burger uses a kafta blend patty. What cheese and toppings would you prefer?"
    
    # Large tabbouleh
    if "tabbouleh" in item_lower and ("large" in item_lower or "big" in item_lower):
        return "Would you like to add any protein to that, like grilled halloumi or chicken?"
    
    # Arak
    if "arak" in item_lower:
        return "Would you like that on the rocks with water?"
    
    # Turkish coffee
    if "turkish coffee" in item_lower or ("coffee" in item_lower and "turkish" in item_lower):
        return "How would you like it: plain, medium sweet, or very sweet?"
    
    # Batata Harra (spicy potatoes)
    if "batata" in item_lower or ("spicy" in item_lower and "potato" in item_lower):
        return "Do you want that regular spice or the extra-hot version?"
    
    # Family orders - Mezze Experience
    if "feast" in item_lower or ("family" in item_lower and ("4" in item_lower or "four" in item_lower)):
        return "The 'Mezze Experience' feeds 4 with 6 mezze items. Is that suitable, or should we build a custom order?"
    
    # Multiple shawarma plates
    if "shawarma" in item_lower and "plate" in item_lower and any(num in item_lower for num in ["two", "2", "three", "3"]):
        return "What sides would you like for the plates: rice or fries?"
    
    # Sambousek orders
    if "sambousek" in item_lower:
        return "We offer beef and lamb sambousek. How many of each would you like?"
    
    # Kibbeh Nayyeh (large platter)
    if "kibbeh nayyeh" in item_lower and ("large" in item_lower or "big" in item_lower):
        return "A large platter serves 6-8 people. When is the earliest you need to pick it up for freshness?"
    
    # Baklava tray
    if "baklava" in item_lower and any(num in item_lower for num in ["20", "dozen", "tray"]):
        return "That is a medium tray. Would you like it packaged with a serving utensil?"
    
    # Multiple items order
    if len(conversation.order_items) > 2 and "mixed grill" in item_lower:
        return "Do you want the mixed grill meats separated, or all together on one platter?"
    
    # Kids meals
    if "kids meal" in item_lower or ("kids" in item_lower and "meal" in item_lower):
        return "What drinks and sides would you like for the kids' meals?"
    
    # Bulk pita / labneh
    if ("pita" in item_lower and any(num in item_lower for num in ["10", "dozen", "large"])) or ("labneh" in item_lower and "kilo" in item_lower):
        return "Would you like the labneh seasoned with olive oil and za'atar?"
    
    # Multiple manakish
    if "manakish" in item_lower and any(num in item_lower for num in ["four", "4", "different"]):
        return "We have Za'atar, Cheese, Kishk, and Spicy Sujuk. Which would you like?"
    
    # Pitcher of lemonade
    if "pitcher" in item_lower and "lemonade" in item_lower:
        return "Will this be sparkling or still lemonade?"
    
    # Sharing recommendations
    if any(phrase in item_lower for phrase in ["6 people", "six people", "sharing", "what's a good way"]):
        return "We recommend our 'Family Mixed Grill' (serves 6) plus three mezze appetizers. Would you like to hear the suggested mezze?"
    
    return None


def _summarize_order(order_items: List[Dict]) -> str:
    """
    Turn the current order into a short spoken summary.
    """
    if not order_items:
        return "I don't have an order on file yet for this call."

    parts = []
    total = 0.0
    for item in order_items:
        qty = item.get("quantity", 1)
        name = item.get("name", "item")
        line_total = float(item.get("total_price", 0.0))
        total += line_total
        parts.append(f"{qty} {name}")

    items_text = ", ".join(parts)
    total_text = f"${total:0.2f}"

    return (
        f"So far I have: {items_text}. The estimated total is {total_text} before tax and fees. "
        "Would you like to add anything else or is that everything?"
    )


def get_conversation(call_sid: str, business_id: str = "restaurant_001") -> ConversationState:
    """
    Get or create conversation state for a call.
    
    Args:
        call_sid: Twilio Call SID
        business_id: Business identifier
        
    Returns:
        ConversationState instance
    """
    if call_sid not in conversations:
        conversations[call_sid] = ConversationState(call_sid, business_id)
        logger.info(f"Created new conversation for call: {call_sid}")
    return conversations[call_sid]


async def process_customer_message(
    text: str,
    call_sid: str,
    business_id: str = "restaurant_001"
) -> str:
    """
    Process customer message and generate response.
    
    This is the main function that processes what the customer said! It:
    1. Classifies the intent (using ML/rule/LLM fallback)
    2. Tries to parse orders from natural language
    3. Answers questions using RAG (or fast path for common questions)
    4. Maintains conversation context
    
    Args:
        text: Customer's transcribed message (what they said)
        call_sid: Twilio Call SID (or session ID for web chat)
        business_id: Business identifier
        
    Returns:
        Generated response text (what the AI should say back)
    """
    try:
        # Get conversation state
        conversation = get_conversation(call_sid, business_id)
        
        # Add customer message to history
        conversation.add_message("user", text)
        
        # Classify intent (auto: tries ML -> rule -> LLM with fallback)
        intent = await classify_intent(text, method="auto")
        conversation.current_intent = intent
        
        logger.info(f"Processing message for call {call_sid}: intent={intent.value}")
        
        text_lower = text.lower()

        # Track response source for logging
        response_source = "unknown"
        
        # --- Handle "yes" confirmations for order additions ---
        # Check if last assistant message asked about adding an item
        if conversation.messages:
            last_assistant_msg = None
            for msg in reversed(conversation.messages):
                if msg.get("role") == "assistant":
                    last_assistant_msg = msg.get("content", "")
                    break
            
            # Check if user said "yes" and last message asked about adding something
            confirmation_words = ["yes", "yeah", "yep", "sure", "ok", "okay", "add it", "add that", "yes please", "yes add"]
            is_confirmation = any(word in text_lower for word in confirmation_words) and len(text_lower.split()) <= 3
            
            if last_assistant_msg and is_confirmation:
                last_msg_lower = last_assistant_msg.lower()
                if "would you like to add" in last_msg_lower or "add.*to your order" in last_msg_lower:
                    # Extract the item name from the last message
                    # Look for patterns like "Baba Ghanoush costs..." or item name before "costs" or "is"
                    import re
                    # Try multiple patterns to find item name
                    item_name = None
                    
                    # Pattern 1: "ItemName costs $X.XX"
                    match1 = re.search(r'^([A-Z][a-zA-Z\s]+?)\s+costs', last_assistant_msg)
                    if match1:
                        item_name = match1.group(1).strip()
                    
                    # Pattern 2: "ItemName is $X.XX"
                    if not item_name:
                        match2 = re.search(r'^([A-Z][a-zA-Z\s]+?)\s+is', last_assistant_msg)
                        if match2:
                            item_name = match2.group(1).strip()
                    
                    # Pattern 3: Look for capitalized words at the start (common for menu items)
                    if not item_name:
                        match3 = re.search(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', last_assistant_msg)
                        if match3:
                            potential_name = match3.group(1).strip()
                            # Check if it's a known menu item
                            for menu_name in MENU_INDEX.keys():
                                if potential_name.lower() in menu_name.lower() or menu_name.lower() in potential_name.lower():
                                    item_name = potential_name
                                    break
                    
                    # Try to find this item in the menu and add it
                    if item_name:
                        for menu_name, menu_item in MENU_INDEX.items():
                            if item_name.lower() in menu_name.lower() or menu_name.lower() in item_name.lower():
                                # Add this item to the order
                                parsed_item = {
                                    "name": menu_item.get("name", item_name),
                                    "quantity": 1,
                                    "unit_price": menu_item.get("price", 0),
                                    "total_price": menu_item.get("price", 0)
                                }
                                # Check if item already exists
                                merged = False
                                for existing_item in conversation.order_items:
                                    if existing_item.get("name") == parsed_item["name"]:
                                        existing_item["quantity"] += 1
                                        existing_item["total_price"] = existing_item["quantity"] * existing_item["unit_price"]
                                        merged = True
                                        break
                                if not merged:
                                    conversation.order_items.append(parsed_item)
                                
                                # Generate confirmation response
                                order_summary = _summarize_order(conversation.order_items)
                                response = f"{order_summary} Would you like to add anything else or is that everything?"
                                response_source = "template_order_parsed"
                                logger.info(f"✅ Added item '{parsed_item['name']}' to order after 'yes' confirmation")
                                conversation.add_message("assistant", response)
                                log_order(
                                    call_sid=call_sid,
                                    business_id=business_id,
                                    customer_text=text,
                                    ai_response=response,
                                    intent=intent,
                                    conversation=conversation,
                                    response_source=response_source,
                                )
                                return response
                    
                    # If we couldn't parse the item but last message asked about adding, just acknowledge
                    if "would you like to add" in last_msg_lower:
                        # Don't add anything, just confirm current order
                        if conversation.order_items:
                            order_summary = _summarize_order(conversation.order_items)
                            response = f"{order_summary} Would you like to add anything else or is that everything?"
                        else:
                            response = "I'd be happy to help you add items to your order. What would you like to add?"
                        response_source = "template_order_parsed"
                        logger.info(f"✅ Handled 'yes' confirmation but couldn't parse item name from: {last_assistant_msg[:50]}")
                        conversation.add_message("assistant", response)
                        log_order(
                            call_sid=call_sid,
                            business_id=business_id,
                            customer_text=text,
                            ai_response=response,
                            intent=intent,
                            conversation=conversation,
                            response_source=response_source,
                        )
                        return response
        
        # --- POS-style order handling ---
        # 0) Check for quantity corrections FIRST (e.g., "no 3 soft drinks not 1")
        import re
        correction_patterns = [
            r"no\s+(\d+)\s+([^,]+?)(?:\s+not\s+(\d+))?",
            r"(\d+)\s+([^,]+?)\s+not\s+(\d+)",
        ]
        correction_match = None
        for pattern in correction_patterns:
            correction_match = re.search(pattern, text_lower)
            if correction_match:
                break
        
        if correction_match and conversation.order_items:
            corrected_qty = int(correction_match.group(1))
            item_desc = correction_match.group(2).strip()
            
            # Simple aliases for common items (same as in _parse_multiple_items)
            item_aliases_local = {
                "coke": "soft drinks", "cokes": "soft drinks", "soda": "soft drinks", 
                "soft drink": "soft drinks", "soft drinks": "soft drinks",
                "fries": "french fries", "french fries": "french fries", 
                "side of fries": "french fries", "sides of fries": "french fries",
            }
            
            # Apply aliases
            for alias, menu_name in item_aliases_local.items():
                if alias in item_desc:
                    item_desc = item_desc.replace(alias, menu_name)
            
            # Find and correct the item
            for existing_item in conversation.order_items:
                item_name_lower = existing_item.get("name", "").lower()
                desc_words = set(item_desc.lower().split())
                name_words = set(item_name_lower.split())
                # Match if key words overlap
                if (item_desc.lower() in item_name_lower or 
                    item_name_lower in item_desc.lower() or
                    len(desc_words.intersection(name_words)) >= 1):
                    old_qty = existing_item.get("quantity", 1)
                    existing_item["quantity"] = corrected_qty
                    existing_item["total_price"] = existing_item["quantity"] * existing_item["unit_price"]
                    logger.info(f"✅ Corrected {existing_item.get('name')} quantity from {old_qty} to {corrected_qty}")
                    order_summary = _summarize_order(conversation.order_items)
                    response = f"{order_summary} Would you like to add anything else or is that everything?"
                    response_source = "template_order_parsed"
                    conversation.add_message("assistant", response)
                    log_order(
                        call_sid=call_sid,
                        business_id=business_id,
                        customer_text=text,
                        ai_response=response,
                        intent=intent,
                        conversation=conversation,
                        response_source=response_source,
                    )
                    return response
        
        # 1) If user asks to repeat the order, answer from order_items directly.
        repeat_phrases = [
            "what was my order",
            "repeat my order",
            "what did i order",
            "read back my order",
            "recap my order",
        ]
        if any(p in text_lower for p in repeat_phrases):
            response = _summarize_order(conversation.order_items)
            response_source = "template_order_repeat"
            # Log order repeat requests
            log_order(
                call_sid=call_sid,
                business_id=business_id,
                customer_text=text,
                ai_response=response,
                intent=intent,
                conversation=conversation,
                response_source=response_source,
            )

        # 2) If user asks about placing an order (but hasn't specified items yet)
        # Check for order intent phrases (handles variations like "hello id like to make an order")
        # IMPORTANT: Check this BEFORE other branches to catch order requests even with greetings
        elif any(phrase in text_lower for phrase in [
            "can i make an order",
            "can i place an order",
            "i want to order",
            "i'd like to order",
            "id like to order",  # Handle "id" without apostrophe
            "i would like to order",
            "would like to order",  # Handles "hello id would like to order"
            "can i order",
            "i want to place an order",
            "how do i order",
            "place an order",
            "make an order",
            "like to make an order",  # Handles "hello id like to make an order"
            "like to place an order",
            "want to make an order",
            "want to place an order"
        ]):
            # If they already have items, summarize and ask if they want to add more
            if conversation.order_items:
                response = (
                    f"{_summarize_order(conversation.order_items)} "
                    "Would you like to add anything else to your order?"
                )
                response_source = "template_order_summary"
            else:
                # Prompt them to tell us what they want
                response = (
                    "Absolutely! I'd be happy to help you place an order. "
                    "What would you like to order today? You can tell me the items and quantities, "
                    "for example, '2 chicken shawarma wraps' or 'a mixed grill plate'."
                )
                response_source = "template_order_prompt"
                logger.info(f"✅ Using PRE-WRITTEN TEMPLATE (no LLM) for order request")
            
            # Log order requests immediately (for both phone and chat)
            log_order(
                call_sid=call_sid,
                business_id=business_id,
                customer_text=text,
                ai_response=response,
                intent=intent,
                conversation=conversation,
                response_source=response_source,
            )

        else:
            # 3) Try to parse order items from the text (handles multiple items)
            order_like_keywords = [
                "order",
                "pickup",
                "takeout",
                "shawarma",
                "wrap",
                "sandwich",
                "kebab",
                "kabob",
                "tray",
                "mixed grill",
                "kabob",
                "hummus",
                "falafel",
                "tabbouleh",
                "fattoush",
                "baklava",
                "fries",
                "coke",
                "soda",
                "soft drink",
            ]

            parsed_items = []
            if any(k in text_lower for k in order_like_keywords):
                # Try to parse multiple items first
                parsed_items = _parse_multiple_items(text)
                
                # If no items found, try single item parser as fallback
                if not parsed_items:
                    single_item = _parse_quantity_and_item(text)
                    if single_item:
                        parsed_items = [single_item]
                
                # Special case: "3 sandwiches" or "2 wraps" without type specified
                if not parsed_items and ("sandwich" in text_lower or "sandwiches" in text_lower or "wrap" in text_lower or "wraps" in text_lower):
                    # Extract quantity
                    import re
                    qty_match = re.search(r"(\d+)\s+(?:sandwich|sandwiches|wrap|wraps)", text_lower)
                    if qty_match:
                        quantity = int(qty_match.group(1))
                        # Ask which type they want
                        response = (
                            f"Great! I'd be happy to help you order {quantity} {'sandwich' if quantity == 1 else 'sandwiches'}. "
                            "Which type would you like? We have:\n"
                            "1. Chicken Shawarma Wrap - $15.50\n"
                            "2. Beef Shawarma Wrap - $16.00\n"
                            "3. Falafel Wrap - $14.00\n"
                            "4. Kafta Wrap - $16.25\n"
                            "Just let me know how many of each you'd like!"
                        )
                        response_source = "template_sandwich_choice"
                        conversation.add_message("assistant", response)
                        log_order(
                            call_sid=call_sid,
                            business_id=business_id,
                            customer_text=text,
                            ai_response=response,
                            intent=intent,
                            conversation=conversation,
                            response_source=response_source,
                        )
                        return response

            if parsed_items:
                # Track the last item added for follow-up questions
                last_added_item = None
                
                # Check if user is correcting a quantity (e.g., "no 3 soft drinks not 1")
                is_correction = any(word in text_lower for word in ["not", "not 1", "not one", "wrong", "incorrect", "should be"])
                
                # Add or merge each parsed item into the order
                for parsed_item in parsed_items:
                    merged = False
                    for existing_item in conversation.order_items:
                        if existing_item.get("name") == parsed_item["name"]:
                            # If this is a correction, replace quantity instead of adding
                            if is_correction:
                                existing_item["quantity"] = parsed_item["quantity"]
                                existing_item["total_price"] = existing_item["quantity"] * existing_item["unit_price"]
                                logger.info(f"✅ Corrected quantity for {parsed_item['name']} to {parsed_item['quantity']}")
                            else:
                                existing_item["quantity"] += parsed_item["quantity"]
                                existing_item["total_price"] = existing_item["quantity"] * existing_item["unit_price"]
                            merged = True
                            break
                    if not merged:
                        conversation.order_items.append(parsed_item)
                        last_added_item = parsed_item["name"]

                # Generate response with follow-up question if applicable
                order_summary = _summarize_order(conversation.order_items)
                
                # Check if we should add a follow-up question
                if last_added_item:
                    followup = _get_order_followup_question(last_added_item, conversation)
                    if followup:
                        response = f"{order_summary} {followup}"
                    else:
                        response = order_summary
                else:
                    response = order_summary
                
                response_source = "template_order_parsed"
                logger.info(f"✅ Using PRE-WRITTEN TEMPLATE (no LLM) for order item parsing")
                
                # Log the order update AFTER response is generated
                log_order(
                    call_sid=call_sid,
                    business_id=business_id,
                    customer_text=text,
                    ai_response=response,
                    intent=intent,
                    conversation=conversation,
                    response_source=response_source,
                )

            else:
                    # --- Check for unrelated questions FIRST (before any template matching) ---
                    unrelated_keywords = [
                        "weather", "temperature", "rain", "snow", "forecast", "sunny", "cloudy",
                        "news", "sports", "politics", "stock", "crypto", "bitcoin",
                        "movie", "tv show", "netflix", "youtube", "streaming",
                        "recipe", "cooking", "how to cook", "how to make",
                        "joke", "tell me a joke", "funny", "entertainment"
                    ]
                    if any(keyword in text_lower for keyword in unrelated_keywords):
                        response = (
                            "I'm here to help with questions about Cedar Garden Lebanese Kitchen - "
                            "our menu, hours, reservations, orders, and location. "
                            "I can't help with general questions like weather, news, or entertainment. "
                            "What can I help you with regarding our restaurant?"
                        )
                        response_source = "template_unrelated"
                        logger.info(f"✅ Using PRE-WRITTEN TEMPLATE for unrelated question (no LLM) - detected: {[k for k in unrelated_keywords if k in text_lower]}")
                    else:
                        # --- Fast path 1: try to answer directly from business data (no LLM) ---
                        direct = answer_from_facts(text)
                        if direct:
                            response = direct
                            response_source = "template_facts"
                            logger.info(f"✅ Using PRE-WRITTEN TEMPLATE from answer_from_facts (no LLM)")
                        else:
                            # --- Fast path 1.5: check follow-up mappings (cost optimization) ---
                            followup_match = None
                            if FOLLOWUP_MAPPINGS:
                                # Try to match against follow-up mappings (fuzzy match)
                                text_lower_clean = ' '.join([w for w in text.lower().split() 
                                                             if w not in ['i', 'a', 'an', 'the', 'just', 'want', 'get', 'one', 'do', 'like', 'would', 'can', 'could', 'please', 'for', 'to', 'with', 'under']])
                                # Check for partial matches
                                for key, template in FOLLOWUP_MAPPINGS.items():
                                    key_words = set(key.lower().split())
                                    text_words = set(text_lower_clean.split())
                                    # If 2+ words match, use this template
                                    if len(key_words.intersection(text_words)) >= 2:
                                        followup_match = template
                                        break
                            
                            if followup_match:
                                response = followup_match
                                response_source = "template_followup_mappings"
                                logger.info(f"✅ Using PRE-WRITTEN TEMPLATE from follow-up mappings (no LLM)")
                            else:
                                # --- Fast path 2: use intent-based templates (no LLM) ---
                                intent_response = answer_from_intent(text, intent)
                                if intent_response:
                                    response = intent_response
                                    response_source = "template_intent"
                                    logger.info(f"✅ Using PRE-WRITTEN TEMPLATE from answer_from_intent (no LLM)")
                                else:
                                    # --- Slow path: use RAG + LLM only when needed (last resort) ---
                                    logger.info(f"⚠️ No template match, using LLM (GPT-4o-mini) for response")
                                    rag = get_rag_system(business_id)

                                    # Retrieve relevant context
                                    retrieved_docs = rag.retrieve(text, n_results=3)
                                    retrieved_context = (
                                        [doc["text"] for doc in retrieved_docs] if retrieved_docs else None
                                    )

                                    # Keep conversation history short to reduce latency
                                    history = conversation.messages[-4:]  # last few turns
                                    result = rag.generate_response(
                                        query=text,
                                        conversation_history=history,
                                        retrieved_context=retrieved_context,
                                    )
                                    # Handle tuple return (response, source) or string (backward compat)
                                    if isinstance(result, tuple):
                                        response, response_source = result
                                    else:
                                        response = result
                                        response_source = "llm_gpt4o_mini"  # Default if not tracked

        # Add assistant response to history
        conversation.add_message("assistant", response)
        
        # Ensure response_source is set (should never be unknown at this point, but safety check)
        if response_source == "unknown":
            # Try to infer from response characteristics
            if "template" in str(response).lower() or len(response) < 200:
                response_source = "template_inferred"
            else:
                response_source = "llm_inferred"
            logger.warning(f"Response source was unknown, inferred as: {response_source}")
        
        # Log ALL order-related conversations (both phone and chat)
        # Check if this looks like an order-related message that should be logged
        order_keywords_for_logging = [
            "order", "pickup", "takeout", "shawarma", "wrap", "kabob", "tray", "mixed grill",
            "sandwich", "sandwiches", "want to order", "like to order", "place an order", "make an order"
        ]
        
        # Log if:
        # 1. Has order keywords AND hasn't been logged yet (not in the excluded list)
        # 2. OR has order items (definitely an order)
        should_log = (
            any(kw in text_lower for kw in order_keywords_for_logging) and
            response_source not in ["template_order_parsed", "template_sandwich_choice", "template_order_prompt", "template_order_summary", "template_order_repeat"]
        ) or conversation.order_items
        
        if should_log:
            log_order(
                call_sid=call_sid,
                business_id=business_id,
                customer_text=text,
                ai_response=response,
                intent=intent,
                conversation=conversation,
                response_source=response_source,
            )

        # If caller indicates they are done, override with a clean closing script
        end_phrases = [
            "that's all",
            "that is all",
            "that's it",
            "that will be all",
            "no that's it",
            "no that's all",
            "no that's everything",
            "i'm done",
            "nothing else",
            "we're good",
            "we are good",
            "that's everything",
            "yes that's it",
            "yes that's all",
        ]
        if any(p in text.lower() for p in end_phrases):
            # If we have an order on file, finalize a kitchen ticket and give a POS-style closing
            if conversation.order_items:
                # Build ticket snapshot for kitchen view
                ticket_items: List[Dict] = []
                total = 0.0
                parts = []
                for item in conversation.order_items:
                    qty = item.get("quantity", 1)
                    name = item.get("name", "item")
                    line_total = float(item.get("total_price", 0.0))
                    total += line_total
                    parts.append(f"{qty} {name}")
                    ticket_items.append(
                        {
                            "name": name,
                            "quantity": qty,
                            "line_total": line_total,
                        }
                    )

                items_text = ", ".join(parts)
                total_text = f"${total:0.2f}"

                conversation.kitchen_ticket = {
                    "items": ticket_items,
                    "total": total,
                    "note": "Pickup in ~25–30 minutes",
                    "status": "pending",
                }

                response = (
                    f"Perfect! Your order is confirmed. You have: {items_text}. "
                    f"The estimated total is {total_text} before tax and fees. "
                    f"Your order will be ready for pickup in approximately 25-30 minutes. "
                    f"We're located at 1840 Cedar Grove Ave, Fullerton, CA 92831. "
                    f"Thank you for choosing Cedar Garden Lebanese Kitchen!"
                )
                response_source = "template_order_finalized"
            else:
                # Fallback closing if no structured order is present
                response = (
                    "Perfect, we've got your request noted. "
                    "If you need to make any changes or have questions, please call us at "
                    "(714) 555-8734. Thank you for calling Cedar Garden, and have a wonderful day!"
                )
                response_source = "template_order_closing"
            
            # Update the last assistant message to this closing line
            conversation.messages[-1]["content"] = response
            
            # Log the finalized order
            log_order(
                call_sid=call_sid,
                business_id=business_id,
                customer_text=text,
                ai_response=response,
                intent=intent,
                conversation=conversation,
                response_source=response_source,
            )

        # Note: Orders are now logged when items are parsed or when order is finalized
        # This ensures we log actual orders, not just mentions of the word "order"

        return response
        
    except Exception as e:
        logger.error(f"Error processing customer message: {str(e)}")
        return "I apologize, but I'm having some technical difficulties. Please try again or call back later."


def clear_conversation(call_sid: str):
    """Clear conversation state (e.g., when call ends)."""
    if call_sid in conversations:
        del conversations[call_sid]
        logger.info(f"Cleared conversation for call: {call_sid}")

