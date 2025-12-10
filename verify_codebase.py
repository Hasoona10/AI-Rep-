#!/usr/bin/env python3
"""
Verification script to check if the codebase is functioning properly.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_imports():
    """Check if all critical imports work."""
    print("=" * 60)
    print("Checking Imports...")
    print("=" * 60)
    
    errors = []
    
    try:
        from backend.ml_models.intent_classifier import IntentClassifier
        print("✓ IntentClassifier import successful")
    except Exception as e:
        errors.append(f"IntentClassifier: {e}")
        print(f"✗ IntentClassifier import failed: {e}")
    
    try:
        from backend.ml_models.feature_extractor import FeatureExtractor
        print("✓ FeatureExtractor import successful")
    except Exception as e:
        errors.append(f"FeatureExtractor: {e}")
        print(f"✗ FeatureExtractor import failed: {e}")
    
    try:
        from backend.ml_models.trainer import train_intent_classifier, train_multiple_models
        print("✓ Trainer functions import successful")
    except Exception as e:
        errors.append(f"Trainer: {e}")
        print(f"✗ Trainer functions import failed: {e}")
    
    try:
        from backend.intents import Intent, classify_intent, classify_intent_ml
        print("✓ Intent classification import successful")
    except Exception as e:
        errors.append(f"Intents: {e}")
        print(f"✗ Intent classification import failed: {e}")
    
    try:
        from backend.evaluation.evaluator import evaluate_on_dataset, compare_all_methods
        print("✓ Evaluation functions import successful")
    except Exception as e:
        errors.append(f"Evaluator: {e}")
        print(f"✗ Evaluation functions import failed: {e}")
    
    try:
        from backend.evaluation.metrics import calculate_metrics
        print("✓ Metrics import successful")
    except Exception as e:
        errors.append(f"Metrics: {e}")
        print(f"✗ Metrics import failed: {e}")
    
    try:
        from backend.ml_models.model_registry import get_registry
        print("✓ Model registry import successful")
    except Exception as e:
        errors.append(f"ModelRegistry: {e}")
        print(f"✗ Model registry import failed: {e}")
    
    try:
        from backend.data.training.synthetic_data import create_training_dataset
        print("✓ Synthetic data generator import successful")
    except Exception as e:
        errors.append(f"SyntheticData: {e}")
        print(f"✗ Synthetic data generator import failed: {e}")
    
    return errors

def check_file_structure():
    """Check if required files exist."""
    print("\n" + "=" * 60)
    print("Checking File Structure...")
    print("=" * 60)
    
    required_files = [
        "backend/ml_models/intent_classifier.py",
        "backend/ml_models/feature_extractor.py",
        "backend/ml_models/trainer.py",
        "backend/ml_models/model_registry.py",
        "backend/intents.py",
        "backend/call_flow.py",
        "backend/evaluation/evaluator.py",
        "backend/evaluation/metrics.py",
        "backend/data/training/synthetic_data.py",
        "scripts/train_model.py",
        "backend/requirements.txt",
    ]
    
    missing = []
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            missing.append(file_path)
            print(f"✗ {file_path} - MISSING")
    
    return missing

def check_class_structure():
    """Check if classes have required methods."""
    print("\n" + "=" * 60)
    print("Checking Class Structure...")
    print("=" * 60)
    
    errors = []
    
    try:
        from backend.ml_models.intent_classifier import IntentClassifier
        classifier = IntentClassifier(algorithm="random_forest")
        
        required_methods = ['train', 'predict', 'save', 'load']
        for method in required_methods:
            if hasattr(classifier, method):
                print(f"✓ IntentClassifier.{method} exists")
            else:
                errors.append(f"IntentClassifier missing method: {method}")
                print(f"✗ IntentClassifier.{method} - MISSING")
    except Exception as e:
        errors.append(f"IntentClassifier structure check failed: {e}")
        print(f"✗ IntentClassifier structure check failed: {e}")
    
    try:
        from backend.ml_models.feature_extractor import FeatureExtractor
        extractor = FeatureExtractor(method="tfidf")
        
        required_methods = ['fit', 'transform', 'fit_transform', 'save', 'load']
        for method in required_methods:
            if hasattr(extractor, method):
                print(f"✓ FeatureExtractor.{method} exists")
            else:
                errors.append(f"FeatureExtractor missing method: {method}")
                print(f"✗ FeatureExtractor.{method} - MISSING")
    except Exception as e:
        errors.append(f"FeatureExtractor structure check failed: {e}")
        print(f"✗ FeatureExtractor structure check failed: {e}")
    
    return errors

def check_training_pipeline():
    """Check if training pipeline functions exist."""
    print("\n" + "=" * 60)
    print("Checking Training Pipeline...")
    print("=" * 60)
    
    errors = []
    
    try:
        from backend.ml_models.trainer import train_intent_classifier, train_multiple_models, load_dataset
        print("✓ train_intent_classifier function exists")
        print("✓ train_multiple_models function exists")
        print("✓ load_dataset function exists")
    except Exception as e:
        errors.append(f"Training pipeline check failed: {e}")
        print(f"✗ Training pipeline check failed: {e}")
    
    return errors

def main():
    """Run all verification checks."""
    print("\n" + "=" * 60)
    print("CODEBASE VERIFICATION")
    print("=" * 60)
    print()
    
    all_errors = []
    
    # Check file structure
    missing_files = check_file_structure()
    all_errors.extend([f"Missing file: {f}" for f in missing_files])
    
    # Check imports
    import_errors = check_imports()
    all_errors.extend(import_errors)
    
    # Check class structure
    structure_errors = check_class_structure()
    all_errors.extend(structure_errors)
    
    # Check training pipeline
    pipeline_errors = check_training_pipeline()
    all_errors.extend(pipeline_errors)
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    if all_errors:
        print(f"\n✗ Found {len(all_errors)} issue(s):")
        for error in all_errors:
            print(f"  - {error}")
        print("\n⚠️  Some issues were found. Please review above.")
        return 1
    else:
        print("\n✓ All checks passed! Codebase appears to be functioning properly.")
        print("\nNote: Import warnings from linter are normal if virtual environment")
        print("      is not configured in your IDE. Runtime imports should work fine.")
        return 0

if __name__ == "__main__":
    sys.exit(main())


