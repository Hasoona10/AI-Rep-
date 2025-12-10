"""
Reservation handling logic.
"""
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from .utils.logger import logger
from .intents import Intent


class ReservationSystem:
    """Handles restaurant reservations."""
    
    def __init__(self, business_id: str = "restaurant_001"):
        """
        Initialize reservation system.
        
        Args:
            business_id: Business identifier
        """
        self.business_id = business_id
        self.reservations_file = Path(f"./data/reservations_{business_id}.json")
        self.reservations_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_reservations()
    
    def _load_reservations(self):
        """Load reservations from JSON file."""
        if self.reservations_file.exists():
            try:
                with open(self.reservations_file, 'r') as f:
                    self.reservations = json.load(f)
            except Exception as e:
                logger.error(f"Error loading reservations: {str(e)}")
                self.reservations = []
        else:
            self.reservations = []
    
    def _save_reservations(self):
        """Save reservations to JSON file."""
        try:
            with open(self.reservations_file, 'w') as f:
                json.dump(self.reservations, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving reservations: {str(e)}")
    
    def check_availability(self, date: datetime, party_size: int) -> bool:
        """
        Check if a time slot is available.
        
        Args:
            date: Requested date/time
            party_size: Number of guests
            
        Returns:
            True if available, False otherwise
        """
        # Simple availability check (in production, integrate with calendar system)
        date_str = date.strftime("%Y-%m-%d")
        time_str = date.strftime("%H:%M")
        
        # Count existing reservations for the same time slot
        conflicting = [
            r for r in self.reservations
            if r.get("status") == "confirmed"
            and r.get("date") == date_str
            and r.get("time") == time_str
        ]
        
        # Simple capacity check (assume max 5 tables per time slot)
        max_tables = 5
        return len(conflicting) < max_tables
    
    def create_reservation(
        self,
        customer_name: str,
        customer_phone: str,
        date: datetime,
        party_size: int,
        special_requests: Optional[str] = None
    ) -> Dict:
        """
        Create a new reservation.
        
        Args:
            customer_name: Customer's name
            customer_phone: Customer's phone number
            date: Reservation date/time
            party_size: Number of guests
            special_requests: Optional special requests
            
        Returns:
            Reservation dictionary
        """
        reservation = {
            "id": f"res_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "business_id": self.business_id,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "date": date.strftime("%Y-%m-%d"),
            "time": date.strftime("%H:%M"),
            "party_size": party_size,
            "special_requests": special_requests,
            "status": "confirmed",
            "created_at": datetime.now().isoformat()
        }
        
        self.reservations.append(reservation)
        self._save_reservations()
        
        logger.info(f"Created reservation: {reservation['id']}")
        return reservation
    
    def parse_reservation_request(self, text: str, intent: Intent) -> Optional[Dict]:
        """
        Parse reservation details from customer text using LLM.
        
        Args:
            text: Customer's message
            intent: Detected intent
            
        Returns:
            Parsed reservation details or None
        """
        if intent != Intent.RESERVATION:
            return None
        
        try:
            from openai import OpenAI
            import os
            
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            prompt = f"""Extract reservation details from this customer message:
"{text}"

Return a JSON object with:
- party_size: number (e.g., 2, 4, 6)
- date: YYYY-MM-DD format (use today if not specified: {datetime.now().strftime('%Y-%m-%d')})
- time: HH:MM format in 24-hour time (e.g., 19:00 for 7pm)
- customer_name: extracted name or null
- special_requests: any special requests or null

If information is missing, use reasonable defaults. Only return valid JSON."""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a reservation parser. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            import json
            parsed = json.loads(response.choices[0].message.content.strip())
            
            # Validate and set defaults
            if "party_size" not in parsed or not parsed["party_size"]:
                parsed["party_size"] = 2
            
            if "date" not in parsed or not parsed["date"]:
                parsed["date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            
            if "time" not in parsed or not parsed["time"]:
                parsed["time"] = "19:00"  # Default 7pm
            
            logger.info(f"Parsed reservation details: {parsed}")
            return parsed
            
        except Exception as e:
            logger.error(f"Error parsing reservation request: {str(e)}")
            return None


# Global reservation system instance
reservation_system: Optional[ReservationSystem] = None

def get_reservation_system(business_id: str = "restaurant_001") -> ReservationSystem:
    """Get or create reservation system instance."""
    global reservation_system
    if reservation_system is None or reservation_system.business_id != business_id:
        reservation_system = ReservationSystem(business_id)
    return reservation_system


