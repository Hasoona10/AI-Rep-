"""
Script to seed business data into ChromaDB.
"""
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.rag import RAGSystem
from backend.utils.logger import logger

def seed_business_data(business_id: str = "restaurant_001"):
    """Seed business data into RAG system."""
    try:
        # Load business data
        business_data_path = Path(__file__).parent.parent / "backend" / "business_data.json"
        
        if not business_data_path.exists():
            logger.error(f"Business data file not found: {business_data_path}")
            return
        
        with open(business_data_path, 'r') as f:
            business_data = json.load(f)
        
        if business_id not in business_data:
            logger.error(f"Business ID {business_id} not found in data file")
            return
        
        biz = business_data[business_id]
        
        # Initialize RAG system
        rag = RAGSystem(business_id=business_id)
        
        # Convert business data to documents
        documents = []
        
        # Hours document
        hours_text = "Business Hours:\n"
        for day, times in biz.get("hours", {}).items():
            hours_text += f"{day.capitalize()}: {times.get('open')} - {times.get('close')}\n"
        documents.append({
            "text": hours_text,
            "metadata": {"type": "hours", "business_id": business_id}
        })
        
        # Menu document
        menu_text = "Menu:\n"
        for category, items in biz.get("menu", {}).items():
            menu_text += f"\n{category.capitalize()}:\n"
            for item in items:
                menu_text += f"- {item.get('name')}: {item.get('price')} - {item.get('description')}\n"
        documents.append({
            "text": menu_text,
            "metadata": {"type": "menu", "business_id": business_id}
        })
        
        # Address document
        addr = biz.get("address", {})
        address_text = f"Address: {addr.get('street')}, {addr.get('city')}, {addr.get('state')} {addr.get('zip')}. Phone: {addr.get('phone')}"
        documents.append({
            "text": address_text,
            "metadata": {"type": "contact", "business_id": business_id}
        })
        
        # Description
        desc_text = biz.get("description", "")
        documents.append({
            "text": desc_text,
            "metadata": {"type": "description", "business_id": business_id}
        })
        
        # Pricing information (extracted from menu)
        pricing_text = "Pricing Information:\n"
        for category, items in biz.get("menu", {}).items():
            for item in items:
                pricing_text += f"{item.get('name')}: {item.get('price')}\n"
        documents.append({
            "text": pricing_text,
            "metadata": {"type": "pricing", "business_id": business_id}
        })
        
        # Add documents to RAG
        rag.add_documents(documents)
        logger.info(f"Successfully seeded {len(documents)} documents for business {business_id}")
        
    except Exception as e:
        logger.error(f"Error seeding business data: {str(e)}")
        raise


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    business_id = os.getenv("DEFAULT_BUSINESS_ID", "restaurant_001")
    seed_business_data(business_id)


