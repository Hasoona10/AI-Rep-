#!/usr/bin/env python3
"""
Process the cedar_garden_order_intents_1500.json file and integrate it into the training system.

This script:
1. Converts the JSON order intents to CSV format for ML training
2. Extracts intent labels (all are ORDER/MENU intents)
3. Creates a mapping for follow-up questions
4. Adds the data to the training dataset
"""
import json
import csv
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.intents import Intent
from backend.utils.logger import logger


def load_order_intents(json_path: Path) -> List[Dict]:
    """Load order intents from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    logger.info(f"Loaded {len(data)} order intent examples from {json_path}")
    return data


def convert_to_training_csv(order_intents: List[Dict], output_path: Path) -> Path:
    """
    Convert order intents to CSV format for ML training.
    
    All these are ORDER/MENU intents, so we'll label them as 'menu' intent
    since they're all about ordering menu items.
    """
    rows = []
    for item in order_intents:
        user_input = item.get('user_input', '').strip()
        if user_input:
            rows.append({
                'text': user_input,
                'intent': 'menu'  # All are menu/order related
            })
    
    # Write to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['text', 'intent'])
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Converted {len(rows)} examples to CSV: {output_path}")
    return output_path


def extract_followup_mappings(order_intents: List[Dict]) -> Dict[str, str]:
    """
    Extract mappings from user input patterns to follow-up questions.
    
    This creates a lookup table that can be used to improve the follow-up
    question system in call_flow.py
    """
    mappings = {}
    
    for item in order_intents:
        user_input = item.get('user_input', '').strip().lower()
        template = item.get('template_or_action', '').strip()
        
        if user_input and template:
            # Extract the actual template text (remove "Template: " prefix)
            if template.startswith('Template: '):
                template_text = template[10:].strip('"')
            elif template.startswith('Action: '):
                template_text = template[8:].strip()
            else:
                template_text = template
            
            # Create a key from the user input (normalized)
            # Use the first few key words that identify the item
            key_words = []
            for word in user_input.split():
                if word not in ['i', 'a', 'an', 'the', 'just', 'want', 'get', 'one', 'do', 'like', 'would', 'can', 'could', 'please', 'for', 'to', 'with', 'under']:
                    key_words.append(word)
                if len(key_words) >= 3:  # Get first 3 meaningful words
                    break
            
            key = ' '.join(key_words[:3])
            if key and template_text:
                mappings[key] = template_text
    
    logger.info(f"Extracted {len(mappings)} follow-up question mappings")
    return mappings


def save_followup_mappings(mappings: Dict[str, str], output_path: Path):
    """Save follow-up question mappings to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(mappings, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved follow-up mappings to {output_path}")


def merge_with_existing_training_data(new_csv_path: Path, existing_csv_path: Path, output_path: Path):
    """
    Merge new order intent data with existing training data.
    
    This combines the new 1500 order examples with the existing synthetic data
    to create a more comprehensive training dataset.
    """
    all_rows = []
    
    # Load existing data if it exists
    if existing_csv_path.exists():
        with open(existing_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                all_rows.append(row)
        logger.info(f"Loaded {len(all_rows)} existing training examples")
    
    # Add new data
    with open(new_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            all_rows.append(row)
    
    # Remove duplicates (based on text)
    seen = set()
    unique_rows = []
    for row in all_rows:
        text = row['text'].lower().strip()
        if text not in seen:
            seen.add(text)
            unique_rows.append(row)
    
    # Write merged data
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['text', 'intent'])
        writer.writeheader()
        writer.writerows(unique_rows)
    
    logger.info(f"Merged dataset: {len(unique_rows)} total examples (removed {len(all_rows) - len(unique_rows)} duplicates)")
    return output_path


def main():
    """Main processing function."""
    project_root = Path(__file__).parent.parent
    
    # Try to find order intent files (set 1 and set 2)
    json_paths = [
        Path("/Users/souna/Downloads/cedar_garden_order_intents_1500.json"),
        Path("/Users/souna/Downloads/cedar_garden_order_intents_1500_set2.json")
    ]
    
    # Find which files exist
    existing_paths = [p for p in json_paths if p.exists()]
    
    if not existing_paths:
        logger.error(f"Order intents files not found in Downloads folder")
        logger.info("Please ensure the files are in your Downloads folder")
        return
    
    logger.info(f"Found {len(existing_paths)} order intent file(s) to process")
    
    # Setup output paths
    data_dir = project_root / "backend" / "data" / "training"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Load order intents from all files
    logger.info("Step 1: Loading order intents from all files...")
    all_order_intents = []
    for json_path in existing_paths:
        logger.info(f"  Loading from: {json_path.name}")
        intents = load_order_intents(json_path)
        all_order_intents.extend(intents)
    
    logger.info(f"Total order intents loaded: {len(all_order_intents)}")
    order_intents = all_order_intents
    
    # Step 2: Convert to training CSV
    logger.info("Step 2: Converting to training CSV format...")
    order_csv = data_dir / "order_intents_train.csv"
    convert_to_training_csv(order_intents, order_csv)
    
    # Step 3: Extract follow-up mappings
    logger.info("Step 3: Extracting follow-up question mappings...")
    mappings = extract_followup_mappings(order_intents)
    mappings_path = data_dir / "order_followup_mappings.json"
    save_followup_mappings(mappings, mappings_path)
    
    # Step 4: Merge with existing training data
    logger.info("Step 4: Merging with existing training data...")
    existing_train = data_dir / "intent_dataset_train.csv"
    merged_train = data_dir / "intent_dataset_train_merged.csv"
    
    if existing_train.exists():
        merge_with_existing_training_data(order_csv, existing_train, merged_train)
        logger.info(f"✅ Merged training data saved to: {merged_train}")
        logger.info(f"   You can use this file to retrain your models with more order examples!")
    else:
        logger.info(f"✅ Order intents CSV saved to: {order_csv}")
        logger.info(f"   No existing training data found - this will be your base dataset")
    
    logger.info(f"\n✅ Processing complete!")
    logger.info(f"   - Training CSV: {order_csv}")
    logger.info(f"   - Follow-up mappings: {mappings_path}")
    if existing_train.exists():
        logger.info(f"   - Merged dataset: {merged_train}")
    logger.info(f"\nNext steps:")
    logger.info(f"   1. Review the follow-up mappings in {mappings_path}")
    logger.info(f"   2. Retrain models using: python scripts/train_model.py")
    logger.info(f"   3. Integrate follow-up mappings into call_flow.py if needed")


if __name__ == "__main__":
    main()

