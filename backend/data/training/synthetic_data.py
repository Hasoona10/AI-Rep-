"""
Generate synthetic training data for intent classification.
"""
import csv
import random
from pathlib import Path
from typing import List, Tuple
from backend.intents import Intent


# Template phrases for each intent category
INTENT_TEMPLATES = {
    Intent.GREETING: [
        "hello", "hi there", "hey", "good morning", "good afternoon", 
        "good evening", "hi how are you", "hey there", "hello there",
        "good day", "morning", "afternoon", "evening", "greetings",
        "hi can you help", "hello I need help", "hey I have a question"
    ],
    Intent.HOURS: [
        "what are your hours", "when are you open", "what time do you open",
        "what time do you close", "are you open today", "what are your operating hours",
        "when do you close", "what time can I come", "are you open now",
        "what days are you open", "what are your business hours",
        "when does the restaurant open", "what time does it close",
        "is the restaurant open", "what are the opening hours",
        "can I come at 7pm", "are you open on weekends", "what about sunday"
    ],
    Intent.MENU: [
        "what's on the menu", "what do you serve", "what food do you have",
        "what dishes are available", "what's for dinner", "what's your special",
        "do you have pasta", "what drinks do you have", "show me the menu",
        "what are your menu items", "what can I order", "what's popular",
        "what do you recommend", "what's good here", "do you have vegetarian options",
        "what kind of food", "tell me about your menu", "what's available"
    ],
    Intent.PRICING: [
        "how much does it cost", "what's the price", "how much is the pasta",
        "what are your prices", "is it expensive", "how much for dinner",
        "what's the cost", "how much money", "what do you charge",
        "how much does dinner cost", "what's the price range", "are prices reasonable",
        "how much for two people", "what's the average price", "do you accept cards",
        "is it affordable", "what's your pricing like"
    ],
    Intent.RESERVATION: [
        "I want to make a reservation", "can I book a table", "reserve a table for 2",
        "I'd like to reserve", "book a table for tonight", "make a reservation for tomorrow",
        "can I reserve a table", "table for 4 please", "book a table",
        "reservation for friday", "can we get a table", "reserve for 7pm",
        "table reservation", "book dinner for 2", "I need a reservation",
        "can you reserve us a table", "make a booking", "reserve a spot"
    ],
    Intent.DIRECTION: [
        "where are you located", "what's your address", "where is the restaurant",
        "how do I get there", "give me directions", "what's the location",
        "where can I find you", "what's your address", "where are you",
        "how to get to the restaurant", "what's the location", "directions please",
        "where is it", "what area are you in", "can you give me the address",
        "how far are you", "what's nearby", "where exactly"
    ],
    Intent.GENERAL_QUESTION: [
        "do you have wifi", "is parking available", "do you take reservations",
        "what's your phone number", "can I call you", "do you deliver",
        "what's your policy", "do you have outdoor seating", "are kids welcome",
        "do you have a bar", "what's your capacity", "do you cater",
        "what payment methods", "do you have parking", "is it wheelchair accessible",
        "what's the dress code", "do you have music", "what's special about this place"
    ],
    Intent.GOODBYE: [
        "thank you", "thanks", "thank you very much", "thanks for your help",
        "goodbye", "bye", "see you later", "thanks bye", "appreciate it",
        "thanks so much", "thank you goodbye", "bye for now", "see you",
        "thank you have a good day", "thanks talk to you later", "appreciate the help"
    ]
}


def generate_synthetic_examples(intent: Intent, num_examples: int = 50) -> List[str]:
    """
    Generate synthetic examples for an intent.
    
    Args:
        intent: Intent class
        num_examples: Number of examples to generate
        
    Returns:
        List of generated text examples
    """
    templates = INTENT_TEMPLATES.get(intent, [])
    if not templates:
        return []
    
    examples = []
    
    # Direct templates
    examples.extend(templates)
    
    # Generate variations
    for _ in range(num_examples - len(templates)):
        base_template = random.choice(templates)
        
        # Add variations
        variations = [
            base_template.capitalize(),
            base_template.upper() if len(base_template) < 20 else base_template,
            f"I'm wondering {base_template}",
            f"Can you tell me {base_template}",
            f"I'd like to know {base_template}",
            base_template + "?",
            base_template + " please",
            "Excuse me, " + base_template,
        ]
        
        examples.append(random.choice(variations))
    
    return examples[:num_examples]


def create_training_dataset(
    output_path: Path,
    examples_per_intent: int = 100,
    train_split: float = 0.8
) -> Tuple[Path, Path]:
    """
    Create training and test datasets.
    
    Args:
        output_path: Path to save the dataset
        examples_per_intent: Number of examples per intent class
        train_split: Ratio of training data (0.8 = 80% train, 20% test)
        
    Returns:
        Tuple of (train_path, test_path)
    """
    # Generate all examples
    all_data = []
    for intent in Intent:
        if intent == Intent.UNKNOWN:
            continue
        
        examples = generate_synthetic_examples(intent, examples_per_intent)
        for example in examples:
            all_data.append({
                'text': example,
                'intent': intent.value
            })
    
    # Shuffle
    random.shuffle(all_data)
    
    # Split train/test
    split_idx = int(len(all_data) * train_split)
    train_data = all_data[:split_idx]
    test_data = all_data[split_idx:]
    
    # Save training set
    train_path = output_path.parent / "intent_dataset_train.csv"
    with open(train_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['text', 'intent'])
        writer.writeheader()
        writer.writerows(train_data)
    
    # Save test set
    test_path = output_path.parent / "intent_dataset_test.csv"
    with open(test_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['text', 'intent'])
        writer.writeheader()
        writer.writerows(test_data)
    
    print(f"Created training dataset: {len(train_data)} examples")
    print(f"Created test dataset: {len(test_data)} examples")
    print(f"Train: {train_path}")
    print(f"Test: {test_path}")
    
    return train_path, test_path


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Create datasets
    output_dir = Path(__file__).parent
    train_path, test_path = create_training_dataset(
        output_dir / "intent_dataset.csv",
        examples_per_intent=100,
        train_split=0.8
    )


