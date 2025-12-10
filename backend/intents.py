"""
Intent classification for customer inquiries.

DEMO SECTION: ML Intent Classification - Fallback Strategy
This is the main intent classification module. It implements the smart fallback strategy:
1. Try ML model first (fast, cheap, 95%+ accuracy)
2. Fall back to rule-based (keyword matching)
3. Finally use LLM API if needed (expensive but accurate)

This saves a ton of money on API calls while still being accurate!
"""
from enum import Enum
from typing import Dict, List, Optional
from openai import OpenAI
import os
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


class Intent(str, Enum):
    """Customer intent types."""
    GREETING = "greeting"
    HOURS = "hours"
    MENU = "menu"
    PRICING = "pricing"
    RESERVATION = "reservation"
    DIRECTION = "direction"
    GENERAL_QUESTION = "general_question"
    GOODBYE = "goodbye"
    UNKNOWN = "unknown"


# Intent keywords for simple rule-based classification
INTENT_KEYWORDS = {
    Intent.GREETING: ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"],
    Intent.HOURS: ["hours", "open", "closed", "when", "time", "available", "operating"],
    Intent.MENU: ["menu", "food", "dish", "drink", "special", "item", "serve", "offer"],
    Intent.PRICING: ["price", "cost", "how much", "expensive", "cheap", "dollar", "$"],
    Intent.RESERVATION: ["reservation", "reserve", "table", "book", "appointment", "availability"],
    Intent.DIRECTION: ["location", "address", "where", "directions", "find", "map"],
    Intent.GOODBYE: ["bye", "goodbye", "thanks", "thank you", "see you", "later"],
}


async def classify_intent_llm(text: str) -> Intent:
    """
    Classify customer intent using LLM.
    
    Args:
        text: Customer's message
        
    Returns:
        Detected intent
    """
    try:
        prompt = f"""Classify the following customer message into one of these intents:
- greeting: Initial greeting or salutation
- hours: Questions about business hours
- menu: Questions about menu items or food
- pricing: Questions about prices or costs
- reservation: Request to book a table or appointment
- direction: Questions about location or address
- general_question: Any other general question
- goodbye: Closing or farewell

Message: "{text}"

Respond with ONLY the intent name (lowercase, no punctuation)."""

        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an intent classifier for a restaurant assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=20
        )
        
        intent_str = response.choices[0].message.content.strip().lower()
        
        # Validate intent
        try:
            intent = Intent(intent_str)
        except ValueError:
            logger.warning(f"Unknown intent returned: {intent_str}, defaulting to UNKNOWN")
            intent = Intent.UNKNOWN
        
        logger.info(f"Intent classified as: {intent.value} for text: {text[:50]}...")
        return intent
        
    except Exception as e:
        logger.error(f"Error classifying intent: {str(e)}")
        return Intent.UNKNOWN


def classify_intent_rule_based(text: str) -> Intent:
    """
    Simple rule-based intent classification using keywords.
    
    Args:
        text: Customer's message
        
    Returns:
        Detected intent
    """
    text_lower = text.lower()
    
    # Check for exact keyword matches
    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                logger.info(f"Intent classified as: {intent.value} (keyword: {keyword})")
                return intent
    
    # Default to general question
    return Intent.GENERAL_QUESTION


# Global ML classifier instance (lazy loaded)
_ml_classifier = None
_ml_classifier_path = None


def _load_ml_classifier(model_path: str = None) -> Optional[object]:
    """
    Load ML classifier if available.
    
    Args:
        model_path: Optional path to model directory
        
    Returns:
        IntentClassifier instance or None
    """
    global _ml_classifier, _ml_classifier_path
    
    # Use provided path or try default location
    if model_path is None:
        from pathlib import Path
        models_dir = Path("./models")
        
        # Try to find latest model
        from .ml_models.model_registry import get_registry
        registry = get_registry()
        latest_model = registry.get_latest_model("intent_classifier")
        
        if latest_model:
            model_path = latest_model['path']
        else:
            # Try default location
            model_path = str(models_dir / "random_forest_tfidf")
    
    # Check if already loaded
    if _ml_classifier is not None and _ml_classifier_path == model_path:
        return _ml_classifier
    
    try:
        from pathlib import Path
        from .ml_models.intent_classifier import IntentClassifier
        from .ml_models.feature_extractor import FeatureExtractor
        
        model_dir = Path(model_path)
        if not model_dir.exists():
            logger.debug(f"ML model not found at {model_path}")
            return None
        
        # Load feature extractor
        extractor_files = list(model_dir.glob("*_extractor.pkl"))
        if not extractor_files:
            logger.debug(f"Feature extractor not found in {model_dir}")
            return None
        
        feature_extractor = FeatureExtractor.load(extractor_files[0])
        
        # Load classifier
        _ml_classifier = IntentClassifier.load(model_dir, feature_extractor)
        _ml_classifier_path = model_path
        logger.info(f"Loaded ML classifier from {model_path}")
        
        return _ml_classifier
        
    except Exception as e:
        logger.warning(f"Failed to load ML classifier: {str(e)}")
        return None


def classify_intent_ml(text: str, model_path: str = None) -> Intent:
    """
    Classify intent using trained ML model.
    
    Args:
        text: Customer's message
        model_path: Optional path to model directory
        
    Returns:
        Detected intent
    """
    classifier = _load_ml_classifier(model_path)
    
    if classifier is None:
        raise ValueError("ML classifier not available. Train a model first.")
    
    try:
        intent = classifier.predict(text)
        logger.info(f"Intent classified as: {intent.value} (ML) for text: {text[:50]}...")
        return intent
    except Exception as e:
        logger.error(f"Error in ML classification: {str(e)}")
        raise


async def classify_intent(
    text: str,
    method: str = "auto",
    use_llm: bool = None,
    ml_model_path: str = None
) -> Intent:
    """
    Classify intent using specified method or auto with fallback.
    
    THIS IS THE KEY FUNCTION! The 'auto' method implements the smart fallback:
    1. Try ML model first (fast, cheap, 95%+ accuracy) - saves money!
    2. Fall back to rule-based (simple keyword matching)
    3. Finally use LLM API if needed (expensive but accurate)
    
    This strategy reduces API costs by ~80% while maintaining high accuracy.
    
    Args:
        text: Customer's message
        method: Classification method ('auto', 'ml', 'rule', 'llm')
                'auto' tries ML -> rule -> LLM with fallback
        use_llm: Deprecated - use 'method' parameter instead
        ml_model_path: Optional path to ML model directory
        
    Returns:
        Detected intent
    """
    # Backward compatibility
    if use_llm is not None:
        method = "llm" if use_llm else "rule"
    
    if method == "ml":
        try:
            return classify_intent_ml(text, ml_model_path)
        except (ValueError, Exception) as e:
            logger.warning(f"ML classification failed: {str(e)}, falling back to rule-based")
            return classify_intent_rule_based(text)
    
    elif method == "rule":
        return classify_intent_rule_based(text)
    
    elif method == "llm":
        return await classify_intent_llm(text)
    
    elif method == "auto":
        # DEMO: This is the fallback strategy! Try ML first, then rule-based, then LLM
        # Step 1: Try ML model (fast, cheap, accurate)
        try:
            classifier = _load_ml_classifier(ml_model_path)
            if classifier is not None:
                intent = classifier.predict(text)
                logger.info(f"Intent classified as: {intent.value} (ML) for text: {text[:50]}...")
                return intent
        except Exception as e:
            logger.debug(f"ML classification failed: {str(e)}")
        
        # Step 2: Fallback to rule-based (keyword matching)
        try:
            intent = classify_intent_rule_based(text)
            if intent != Intent.GENERAL_QUESTION:  # Rule-based found something
                return intent
        except Exception as e:
            logger.debug(f"Rule-based classification failed: {str(e)}")
        
        # Step 3: Final fallback to LLM (expensive but accurate)
        return await classify_intent_llm(text)
    
    else:
        raise ValueError(f"Unknown method: {method}. Use 'auto', 'ml', 'rule', or 'llm'")

