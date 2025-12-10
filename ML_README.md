# Machine Learning Implementation Guide

This document describes the ML components added to the AI Receptionist system.

## Overview

The project now includes a **trained intent classifier** that can be used alongside rule-based and LLM-based classification methods. This provides:

- **Faster inference** (local ML model vs. API calls)
- **Lower cost** (no per-request API charges)
- **Better reliability** (no dependency on external APIs)
- **ML project requirements** (model training, evaluation, comparison)

## Architecture

### Components

1. **Feature Extractor** (`backend/ml_models/feature_extractor.py`)
   - TF-IDF vectorization
   - Bag-of-words (BOW)
   - PCA dimensionality reduction option

2. **Intent Classifier** (`backend/ml_models/intent_classifier.py`)
   - Supports multiple algorithms:
     - Random Forest
     - Logistic Regression
     - SVM
     - Gradient Boosting
     - Neural Network (MLP)

3. **Training Pipeline** (`backend/ml_models/trainer.py`)
   - Dataset loading
   - Feature extraction
   - Model training with cross-validation
   - Model comparison

4. **Evaluation Framework** (`backend/evaluation/`)
   - Metrics calculation (accuracy, F1, precision, recall)
   - Confusion matrices
   - Model comparison (ML vs. rule vs. LLM)
   - Classification reports

5. **Model Registry** (`backend/ml_models/model_registry.py`)
   - Version tracking
   - Metadata management
   - Best model selection

## Quick Start

### 1. Install Dependencies

```bash
cd ai-assistant/backend
pip install -r requirements.txt
```

### 2. Generate Training Data

```bash
cd ai-assistant
python scripts/train_model.py
```

This will:
- Generate synthetic training data (~800 examples)
- Train multiple model configurations
- Evaluate and compare all methods
- Save models to `models/` directory

### 3. Use Trained Model

The system automatically uses the trained ML model if available. The classification method follows this fallback chain:

```
ML Model → Rule-based → LLM API
```

You can also explicitly choose a method:

```python
from backend.intents import classify_intent

# Auto (tries ML -> rule -> LLM)
intent = await classify_intent(text, method="auto")

# ML only
intent = classify_intent(text, method="ml")  # Note: synchronous

# Rule-based only
intent = classify_intent(text, method="rule")

# LLM only
intent = await classify_intent(text, method="llm")
```

## Training Your Own Model

### Generate Dataset

```python
from backend.data.training.synthetic_data import create_training_dataset
from pathlib import Path

train_path, test_path = create_training_dataset(
    Path("data/training/intent_dataset.csv"),
    examples_per_intent=100,  # Number of examples per intent class
    train_split=0.8  # 80% train, 20% test
)
```

### Train Single Model

```python
from backend.ml_models.trainer import train_intent_classifier
from pathlib import Path

classifier, results = train_intent_classifier(
    train_data_path=Path("data/training/intent_dataset_train.csv"),
    algorithm="random_forest",  # or "logistic", "svm", etc.
    feature_method="tfidf",  # or "bow", "tfidf_pca"
    model_output_dir=Path("models/my_model"),
    test_size=0.2
)

print(f"Training accuracy: {results['training_accuracy']:.4f}")
print(f"CV accuracy: {results['cv_mean']:.4f} (+/- {results['cv_std']:.4f})")
```

### Train Multiple Models

```python
from backend.ml_models.trainer import train_multiple_models
from pathlib import Path

results = train_multiple_models(
    train_data_path=Path("data/training/intent_dataset_train.csv"),
    algorithms=["random_forest", "logistic", "svm"],
    feature_methods=["tfidf"],
    models_dir=Path("models")
)

# Results contain metrics for all configurations
for config_name, metrics in results.items():
    print(f"{config_name}: {metrics.get('validation_accuracy', 0):.4f}")
```

## Evaluation

### Evaluate All Methods

```python
from backend.evaluation.evaluator import compare_all_methods
from backend.ml_models.intent_classifier import IntentClassifier
from backend.ml_models.feature_extractor import FeatureExtractor
from pathlib import Path

# Load your trained model
model_dir = Path("models/random_forest_tfidf")
extractor = FeatureExtractor.load(model_dir / "tfidf_extractor.pkl")
classifier = IntentClassifier.load(model_dir, extractor)

# Compare all methods
comparison = compare_all_methods(
    test_data_path=Path("data/training/intent_dataset_test.csv"),
    ml_classifier=classifier,
    output_dir=Path("evaluation_results")
)

print(f"Best Model: {comparison['best_model_accuracy']}")
print(f"Accuracy: {comparison['best_accuracy']:.4f}")
```

### Calculate Metrics

```python
from backend.evaluation.metrics import calculate_metrics, plot_confusion_matrix

# Assuming you have predictions
y_true = ["reservation", "menu", "hours", ...]
y_pred = ["reservation", "menu", "hours", ...]

metrics = calculate_metrics(y_true, y_pred)
print(f"Accuracy: {metrics['accuracy']:.4f}")
print(f"F1 Score: {metrics['f1_weighted']:.4f}")

# Plot confusion matrix
plot_confusion_matrix(
    y_true, y_pred,
    output_path=Path("confusion_matrix.png")
)
```

## Model Registry

Track and manage multiple model versions:

```python
from backend.ml_models.model_registry import get_registry
from pathlib import Path

registry = get_registry(Path("models/registry.json"))

# Register a model
version_id = registry.register_model(
    model_name="intent_classifier",
    model_path=Path("models/random_forest_tfidf"),
    algorithm="random_forest",
    feature_method="tfidf",
    metrics={"accuracy": 0.95, "f1_weighted": 0.94},
    metadata={"description": "Best model so far"}
)

# Get latest model
latest = registry.get_latest_model("intent_classifier")

# Get best model by metric
best = registry.get_best_model("intent_classifier", metric="accuracy")

# List all models
all_models = registry.list_models()
```

## Project Structure

```
ai-assistant/
├── backend/
│   ├── ml_models/
│   │   ├── feature_extractor.py      # Feature extraction
│   │   ├── intent_classifier.py      # ML classifier
│   │   ├── trainer.py                 # Training pipeline
│   │   └── model_registry.py          # Model versioning
│   ├── evaluation/
│   │   ├── metrics.py                 # Evaluation metrics
│   │   └── evaluator.py               # Evaluation pipeline
│   ├── data/
│   │   └── training/
│   │       ├── synthetic_data.py      # Dataset generator
│   │       ├── intent_dataset_train.csv
│   │       └── intent_dataset_test.csv
│   └── intents.py                     # Updated with ML support
├── models/                            # Trained models
│   ├── random_forest_tfidf/
│   ├── logistic_tfidf/
│   └── registry.json
├── evaluation_results/                # Evaluation outputs
│   ├── comparison_report.txt
│   ├── confusion_matrix_ml.png
│   └── classification_report_ml.txt
└── scripts/
    └── train_model.py                 # Training script
```

## ML Project Requirements Fulfillment

This implementation fulfills typical ML project requirements:

### ✅ Implementation Lifecycle
- Data collection/generation
- Feature engineering
- Model training
- Evaluation
- Comparison

### ✅ Report Sections

1. **What has been done before?**
   - Intent classification in chatbots
   - Restaurant assistant systems
   - RAG-based conversational AI

2. **What are you trying to do differently?**
   - Multi-channel approach (phone + web)
   - ML model comparison (ML vs. rule vs. LLM)
   - Hybrid fallback strategy

3. **What is your implementation?**
   - Trained ML classifier (Random Forest, SVM, etc.)
   - Feature extraction (TF-IDF, BOW)
   - Evaluation framework
   - Model comparison system

4. **Analyze the results**
   - Accuracy, F1, precision, recall metrics
   - Confusion matrices
   - Per-class performance

5. **Compare your results with others'**
   - ML model vs. rule-based vs. LLM API
   - Multiple algorithm comparison
   - Performance benchmarks

6. **Lessons learned**
   - When to use each method
   - Trade-offs (accuracy vs. cost vs. latency)
   - Best practices for production

## Next Steps

1. **Collect Real Data**: Replace synthetic data with real customer conversations
2. **Fine-tune Models**: Experiment with hyperparameters
3. **Add More Features**: Include context features (time of day, day of week, etc.)
4. **A/B Testing**: Implement model comparison in production
5. **Monitoring**: Track model performance over time

## Troubleshooting

### Model Not Found Error

If you get "ML classifier not available":
1. Train a model first: `python scripts/train_model.py`
2. Check that models are in the `models/` directory
3. Verify the model registry has entries

### Import Errors

Make sure all dependencies are installed:
```bash
pip install scikit-learn numpy pandas matplotlib joblib
```

### Low Accuracy

- Increase training data (more examples per intent)
- Try different algorithms
- Experiment with feature extraction methods
- Add more domain-specific templates to synthetic data generator


