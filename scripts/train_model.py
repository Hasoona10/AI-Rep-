#!/usr/bin/env python3
"""
Script to train intent classification models.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.data.training.synthetic_data import create_training_dataset
from backend.ml_models.trainer import train_multiple_models, train_intent_classifier
from backend.evaluation.evaluator import compare_all_methods
from backend.ml_models.model_registry import get_registry
from backend.utils.logger import logger
from dotenv import load_dotenv

load_dotenv()


def main():
    """Main training pipeline."""
    logger.info("Starting model training pipeline...")
    
    # Setup paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "backend" / "data" / "training"
    models_dir = project_root / "models"
    test_data_path = project_root / "backend" / "data" / "training" / "intent_dataset_test.csv"
    
    # Step 1: Generate training data if it doesn't exist
    train_data_path = data_dir / "intent_dataset_train.csv"
    if not train_data_path.exists() or not test_data_path.exists():
        logger.info("Generating synthetic training data...")
        train_data_path, test_data_path = create_training_dataset(
            data_dir / "intent_dataset.csv",
            examples_per_intent=100,
            train_split=0.8
        )
    
    # Step 2: Train models
    logger.info("\n" + "="*60)
    logger.info("Training Multiple Models")
    logger.info("="*60)
    
    results = train_multiple_models(
        train_data_path=train_data_path,
        algorithms=["random_forest", "logistic", "svm"],
        feature_methods=["tfidf"],
        models_dir=models_dir
    )
    
    # Step 3: Register best model
    registry = get_registry(models_dir / "registry.json")
    best_model_name = None
    best_accuracy = -1
    
    for config_name, result in results.items():
        if 'error' in result:
            continue
        
        accuracy = result.get('validation_accuracy', result.get('cv_mean', 0))
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_model_name = config_name
    
    if best_model_name:
        logger.info(f"\nBest model: {best_model_name} (accuracy: {best_accuracy:.4f})")
        
        # Register in registry
        algorithm, feature_method = best_model_name.split('_', 1)
        registry.register_model(
            model_name="intent_classifier",
            model_path=models_dir / best_model_name,
            algorithm=algorithm,
            feature_method=feature_method,
            metrics={
                'accuracy': best_accuracy,
                **{k: v for k, v in results[best_model_name].items() 
                   if k not in ['algorithm', 'feature_method']}
            }
        )
    
    # Step 4: Evaluate all methods
    logger.info("\n" + "="*60)
    logger.info("Evaluating All Methods")
    logger.info("="*60)
    
    # Load best ML model
    ml_classifier = None
    if best_model_name:
        from backend.ml_models.intent_classifier import IntentClassifier
        from backend.ml_models.feature_extractor import FeatureExtractor
        
        model_dir = models_dir / best_model_name
        extractor_path = list(model_dir.glob("*_extractor.pkl"))[0]
        feature_extractor = FeatureExtractor.load(extractor_path)
        ml_classifier = IntentClassifier.load(model_dir, feature_extractor)
    
    # Compare all methods
    evaluation_dir = project_root / "evaluation_results"
    comparison = compare_all_methods(
        test_data_path=test_data_path,
        ml_classifier=ml_classifier,
        output_dir=evaluation_dir
    )
    
    logger.info("\n" + "="*60)
    logger.info("Training Complete!")
    logger.info("="*60)
    logger.info(f"Best Model (Accuracy): {comparison['best_model_accuracy']} ({comparison['best_accuracy']:.4f})")
    logger.info(f"Best Model (F1): {comparison['best_model_f1']} ({comparison['best_f1']:.4f})")
    logger.info(f"\nResults saved to: {evaluation_dir}")


if __name__ == "__main__":
    main()


