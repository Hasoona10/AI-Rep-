"""
Retrieval-Augmented Generation (RAG) using ChromaDB.

DEMO SECTION: RAG System & Business Intelligence
This is the RAG (Retrieval-Augmented Generation) system! It uses ChromaDB (a vector database)
to store business information like menu items, hours, prices, etc. When a customer asks
a question, it searches the database for relevant info and uses that context to generate
accurate responses. This ensures the AI always has current, accurate business data.
"""
import os
import json
import hashlib
from typing import List, Dict, Optional
from openai import OpenAI
import chromadb
from chromadb.config import Settings
from pathlib import Path
from datetime import datetime, timedelta
from collections import OrderedDict
from .utils.logger import logger

# Lazy initialization - client will be created when needed
_client = None

def get_openai_client():
    """Get or create OpenAI client with API key from environment."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set. Make sure .env file is loaded.")
        _client = OpenAI(api_key=api_key)
    return _client


def load_business_data(business_data_path: Path) -> Dict:
    """
    Load business data from JSON file.
    
    Args:
        business_data_path: Path to business_data.json
        
    Returns:
        Business data dictionary
    """
    try:
        with open(business_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded business data from {business_data_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading business data: {str(e)}")
        raise


def make_chunks(biz_data: Dict) -> List[Dict]:
    """
    Convert business data JSON into text chunks for vector storage.
    
    Args:
        biz_data: Business data dictionary
        
    Returns:
        List of chunk dictionaries with 'text', 'id', and 'metadata'
    """
    chunks = []
    business_name = biz_data.get("business_name", "Restaurant")
    
    # Chunk 1: Basic info (name, description, contact)
    address = biz_data.get("address", {})
    if isinstance(address, dict):
        address_str = f"{address.get('street', '')}, {address.get('city', '')}, {address.get('state', '')} {address.get('zip', '')}"
        phone = address.get('phone', '')
    else:
        address_str = str(address)
        phone = ""
    
    basic_info = f"{business_name}: {biz_data.get('description', '')} "
    basic_info += f"Located at {address_str}. Phone: {phone}."
    if address.get('website'):
        basic_info += f" Website: {address.get('website')}."
    
    chunks.append({
        "id": "basic_info",
        "text": basic_info,
        "metadata": {"type": "basic_info", "section": "overview"}
    })
    
    # Chunk 2: Hours + Location info
    hours = biz_data.get("hours", {})
    hours_text = f"{business_name} hours: "
    hours_list = [f"{day.capitalize()}: {time}" for day, time in hours.items()]
    hours_text += "; ".join(hours_list)
    
    location_info = biz_data.get("location_info", {})
    if location_info:
        hours_text += f" Location: {address_str}."
        if location_info.get("parking"):
            hours_text += f" Parking: {location_info['parking']}"
        if location_info.get("landmarks"):
            hours_text += f" {location_info['landmarks']}"
        if location_info.get("public_transport"):
            hours_text += f" {location_info['public_transport']}"
    
    chunks.append({
        "id": "hours_location",
        "text": hours_text,
        "metadata": {"type": "hours", "section": "hours_location"}
    })
    
    # Chunk 3: Menu items (one chunk per menu section)
    menu_sections = biz_data.get("menu_sections", [])
    for section in menu_sections:
        section_name = section.get("name", "")
        section_text = f"Menu - {section_name}: "
        items_text = []
        
        for item in section.get("items", []):
            item_name = item.get("name", "")
            price = item.get("price", "")
            description = item.get("description", "")
            tags = item.get("tags", [])
            
            item_str = f"{item_name}"
            if price:
                if isinstance(price, (int, float)):
                    item_str += f" - ${price:.2f}"
                else:
                    item_str += f" - {price}"
            if description:
                item_str += f". {description}"
            if tags:
                item_str += f" Tags: {', '.join(tags)}"
            
            items_text.append(item_str)
        
        section_text += " | ".join(items_text)
        chunks.append({
            "id": f"menu_{section_name.lower().replace(' ', '_')}",
            "text": section_text,
            "metadata": {"type": "menu", "section": section_name}
        })
    
    # Chunk 4: FAQ (one chunk per FAQ item)
    faq_items = biz_data.get("faq", [])
    for i, faq in enumerate(faq_items):
        faq_text = f"Q: {faq.get('question', '')} A: {faq.get('answer', '')}"
        chunks.append({
            "id": f"faq_{i}",
            "text": faq_text,
            "metadata": {"type": "faq", "index": i}
        })
    
    # Chunk 5: Policies
    policies = biz_data.get("policies", {})
    if policies:
        policies_text = f"{business_name} policies: "
        policy_items = []
        for key, value in policies.items():
            policy_items.append(f"{key.replace('_', ' ').title()}: {value}")
        policies_text += " | ".join(policy_items)
        
        chunks.append({
            "id": "policies",
            "text": policies_text,
            "metadata": {"type": "policies", "section": "policies"}
        })
    
    # Chunk 6: Reservation rules
    reservation_rules = biz_data.get("reservation_rules", {})
    if reservation_rules:
        rules_text = f"Reservation information: "
        rules_text += f"Reservations accepted for parties of {reservation_rules.get('min_party_size', 1)} to {reservation_rules.get('max_party_size', 10)}. "
        if reservation_rules.get('requires_phone_for_large_parties'):
            large_threshold = reservation_rules.get('large_party_threshold', 8)
            rules_text += f"Parties of {large_threshold} or more should call ahead. "
        if reservation_rules.get('lead_time_minutes'):
            rules_text += f"Please call at least {reservation_rules['lead_time_minutes']} minutes in advance. "
        if reservation_rules.get('advance_booking_days'):
            rules_text += f"Reservations can be made up to {reservation_rules['advance_booking_days']} days in advance."
        
        chunks.append({
            "id": "reservation_rules",
            "text": rules_text,
            "metadata": {"type": "reservation", "section": "reservation_rules"}
        })
    
    # Chunk 7: Special notes
    special_notes = biz_data.get("special_notes", [])
    if special_notes:
        notes_text = f"{business_name} special information: " + " | ".join(special_notes)
        chunks.append({
            "id": "special_notes",
            "text": notes_text,
            "metadata": {"type": "special_notes", "section": "notes"}
        })
    
    logger.info(f"Created {len(chunks)} chunks from business data")
    return chunks


def seed_vectordb(business_data_path: Path, business_id: str = "restaurant_001", clear_existing: bool = False):
    """
    Seed the vector database with business data chunks.
    
    Args:
        business_data_path: Path to business_data.json
        business_id: Business identifier
        clear_existing: Whether to clear existing data before seeding
    """
    try:
        logger.info(f"Seeding vector database for business: {business_id}")
        
        # Load business data
        biz_data = load_business_data(business_data_path)
        
        # Make chunks
        chunks = make_chunks(biz_data)
        
        # Initialize RAG system
        rag = RAGSystem(business_id=business_id)
        
        # Clear existing collection if requested
        if clear_existing:
            try:
                rag.chroma_client.delete_collection(name=rag.collection.name)
                rag.collection = rag.chroma_client.create_collection(
                    name=rag.collection.name,
                    metadata={"business_id": business_id}
                )
                logger.info(f"Cleared existing collection: {rag.collection.name}")
            except:
                pass
        
        # Convert chunks to documents format
        documents = []
        for chunk in chunks:
            documents.append({
                "text": chunk["text"],
                "metadata": {
                    **chunk["metadata"],
                    "chunk_id": chunk["id"]
                }
            })
        
        # Add to vector store
        rag.add_documents(documents)
        
        logger.info(f"Successfully seeded vector database with {len(chunks)} chunks")
        return rag
        
    except Exception as e:
        logger.error(f"Error seeding vector database: {str(e)}")
        raise


# Response cache for LLM calls (reduces API costs)
# Uses LRU cache with TTL (24 hours)
_response_cache: OrderedDict = OrderedDict()
_cache_max_size = 500  # Max 500 cached responses
_cache_ttl_hours = 24  # Cache expires after 24 hours


def _get_cache_key(query: str, context_hash: str = "") -> str:
    """Generate cache key from query and context."""
    key_string = f"{query.lower().strip()}:{context_hash}"
    return hashlib.md5(key_string.encode()).hexdigest()


def _get_cached_response(cache_key: str) -> Optional[str]:
    """Get cached response if it exists and hasn't expired."""
    if cache_key not in _response_cache:
        return None
    
    cached_item = _response_cache[cache_key]
    # Check if expired (24 hour TTL)
    if datetime.now() - cached_item['timestamp'] > timedelta(hours=_cache_ttl_hours):
        _response_cache.pop(cache_key)
        return None
    
    # Move to end (LRU)
    _response_cache.move_to_end(cache_key)
    return cached_item['response']


def _cache_response(cache_key: str, response: str):
    """Cache a response."""
    _response_cache[cache_key] = {
        'response': response,
        'timestamp': datetime.now()
    }
    
    # Enforce max size (remove oldest if over limit)
    if len(_response_cache) > _cache_max_size:
        _response_cache.popitem(last=False)  # Remove oldest


class RAGSystem:
    """RAG system for retrieving business information."""
    
    def __init__(self, business_id: str = "default", db_path: str = "./chroma_db"):
        """
        Initialize RAG system with ChromaDB.
        
        Args:
            business_id: Unique identifier for the business
            db_path: Path to ChromaDB directory
        """
        self.business_id = business_id
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        collection_name = f"business_{business_id}"
        try:
            self.collection = self.chroma_client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except:
            self.collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"business_id": business_id}
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def _embed_text(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts using OpenAI.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        client = get_openai_client()
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [item.embedding for item in response.data]
    
    def add_documents(self, documents: List[Dict[str, str]]):
        """
        Add documents to the vector store.
        
        Args:
            documents: List of dicts with 'text' and optional 'metadata'
        """
        try:
            texts = [doc["text"] for doc in documents]
            metadatas = [doc.get("metadata", {}) for doc in documents]
            ids = [f"{self.business_id}_{i}" for i in range(len(documents))]
            
            # Generate embeddings in batch
            embeddings = self._embed_text(texts)
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to collection")
            
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise
    
    def retrieve(self, query: str, n_results: int = 3) -> List[Dict]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of relevant documents with metadata
        """
        try:
            # Check if query is completely unrelated to restaurant business
            # If so, return empty to avoid confusing LLM with irrelevant context
            query_lower = query.lower()
            unrelated_keywords = [
                "weather", "temperature", "rain", "snow", "forecast",
                "news", "sports", "politics", "stock", "crypto",
                "movie", "tv show", "netflix", "youtube"
            ]
            if any(keyword in query_lower for keyword in unrelated_keywords):
                logger.info(f"Query '{query[:50]}...' is unrelated to restaurant, skipping RAG retrieval")
                return []
            
            # Generate query embedding
            query_embeddings = self._embed_text([query])
            query_embedding = query_embeddings[0]
            
            # Search collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Format results
            retrieved_docs = []
            if results["documents"] and len(results["documents"][0]) > 0:
                for i in range(len(results["documents"][0])):
                    retrieved_docs.append({
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0
                    })
            
            logger.info(f"Retrieved {len(retrieved_docs)} documents for query: {query[:50]}...")
            return retrieved_docs
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return []
    
    def generate_response(
        self,
        query: str,
        conversation_history: Optional[List[Dict]] = None,
        retrieved_context: Optional[List[str]] = None
    ) -> str:
        """
        Generate response using GPT-4o with retrieved context.
        
        COST OPTIMIZATION: Uses response caching to avoid duplicate LLM calls.
        Cached responses are valid for 24 hours.
        
        Args:
            query: User's question
            conversation_history: Previous conversation messages
            retrieved_context: Retrieved document texts
            
        Returns:
            Generated response
        """
        try:
            # Build context from retrieved documents
            context_text = ""
            if retrieved_context:
                context_text = "\n\n".join(retrieved_context)
            
            # Check cache first (cost optimization)
            context_hash = hashlib.md5(context_text.encode()).hexdigest() if context_text else ""
            cache_key = _get_cache_key(query, context_hash)
            cached_response = _get_cached_response(cache_key)
            
            if cached_response:
                logger.info(f"✅ Using CACHED response (no LLM call) for query: {query[:50]}...")
                return cached_response, "llm_cached"  # Return response and source
            
            # Build conversation history
            messages = [
                {
                    "role": "system",
                    "content": """You are a friendly and helpful AI receptionist for Cedar Garden Lebanese Kitchen. 
Use the provided business information to answer customer questions accurately. 
Be concise, professional, and warm. 

IMPORTANT: If a customer asks about placing an order or making an order, encourage them to tell you what they'd like to order. 
For regular takeout orders, we can process them immediately. For large catering orders (party trays), we typically need 24-48 hours notice.

If you don't know something, politely say so and offer to connect them with staff."""
                }
            ]
            
            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current query with context
            user_message = query
            if context_text:
                user_message = f"""Business Information:
{context_text}

Customer Question: {query}

Please answer the customer's question using the business information above."""
            
            messages.append({"role": "user", "content": user_message})
            
            # Generate response
            client = get_openai_client()
            response = client.chat.completions.create(
                model="gpt-4o-mini",   # faster, cheaper, good for phone replies
                messages=messages,
                temperature=0.3,        # COST OPT: Lower temp = more deterministic, slightly cheaper
                max_tokens=150         # COST OPT: Reduced from 220 to save tokens
            )
            
            generated_text = response.choices[0].message.content.strip()
            logger.info(f"⚠️ Generated NEW response (LLM call) for query: {query[:50]}...")
            
            # Cache the response for future use
            _cache_response(cache_key, generated_text)
            
            return generated_text, "llm_gpt4o_mini"  # Return response and source
                
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again or call back later.", "llm_error"


# Global RAG instance (will be initialized in main.py)
rag_system: Optional[RAGSystem] = None

def get_rag_system(business_id: str = "default") -> RAGSystem:
    """Get or create RAG system instance."""
    global rag_system
    if rag_system is None or rag_system.business_id != business_id:
        rag_system = RAGSystem(business_id=business_id)
    return rag_system

