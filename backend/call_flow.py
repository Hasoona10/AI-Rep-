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
                "If you have any specific questions or allergies, we’re happy to help."
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
    }
    for wrong, right in replacements.items():
        q = q.replace(wrong, right)

    # 1) Quantity: prefer explicit digit, then small number words
    qty_match = re.search(r"(?:^|\\s)(\\d+)(?:\\s+)", q)
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
            if re.search(rf"\\b{word}\\b", q):
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

        # --- POS-style order handling ---
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

        else:
            # 2) Try to parse an order line from the text and append to order
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
            ]

            parsed_line = None
            if any(k in text_lower for k in order_like_keywords):
                parsed_line = _parse_quantity_and_item(text)

            if parsed_line:
                # Add or merge into existing items
                merged = False
                for item in conversation.order_items:
                    if item.get("name") == parsed_line["name"]:
                        item["quantity"] += parsed_line["quantity"]
                        item["total_price"] = item["quantity"] * item["unit_price"]
                        merged = True
                        break
                if not merged:
                    conversation.order_items.append(parsed_line)

                response = _summarize_order(conversation.order_items)

            else:
                # --- Fast path: try to answer directly from business data (no LLM) ---
                direct = answer_from_facts(text)
                if direct:
                    response = direct
                else:
                    # --- Slow path: use RAG + LLM only when needed ---
                    rag = get_rag_system(business_id)

                    # Retrieve relevant context
                    retrieved_docs = rag.retrieve(text, n_results=3)
                    retrieved_context = (
                        [doc["text"] for doc in retrieved_docs] if retrieved_docs else None
                    )

                    # Keep conversation history short to reduce latency
                    history = conversation.messages[-4:]  # last few turns
                    response = rag.generate_response(
                        query=text,
                        conversation_history=history,
                        retrieved_context=retrieved_context,
                    )

        # Add assistant response to history
        conversation.add_message("assistant", response)

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
                    f"Perfect, I’ve placed your order for {items_text} with an estimated total of "
                    f"{total_text} before tax and fees. Your order will be ready in about "
                    "25 to 30 minutes at Cedar Garden Lebanese Kitchen. "
                    "If you need to make any changes, please call us back at (714) 555-8734. "
                    "Thank you for calling Cedar Garden, and have a wonderful day!"
                )
            else:
                # Fallback closing if no structured order is present
                response = (
                    "Perfect, we’ve got your request noted. "
                    "If you need to make any changes, please call us back at "
                    "(714) 555-8734. Thank you for calling Cedar Garden, and have a wonderful day!"
                )
            # Update the last assistant message to this closing line
            conversation.messages[-1]["content"] = response

        # Heuristic: log messages that look like orders for demo purposes
        order_keywords = [
            "order",
            "pickup",
            "takeout",
            "shawarma",
            "wrap",
            "kabob",
            "kebab",
            "tray",
            "mixed grill",
        ]
        if any(kw in text_lower for kw in order_keywords):
            log_order(
                call_sid=call_sid,
                business_id=business_id,
                customer_text=text,
                ai_response=response,
                intent=intent,
                conversation=conversation,
            )

        return response
        
    except Exception as e:
        logger.error(f"Error processing customer message: {str(e)}")
        return "I apologize, but I'm having some technical difficulties. Please try again or call back later."


def clear_conversation(call_sid: str):
    """Clear conversation state (e.g., when call ends)."""
    if call_sid in conversations:
        del conversations[call_sid]
        logger.info(f"Cleared conversation for call: {call_sid}")

