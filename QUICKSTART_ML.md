# Quick Start: ML Features

## Install ML Dependencies

```bash
cd ai-assistant/backend
pip install scikit-learn numpy pandas matplotlib joblib
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

## Train Your First Model

```bash
cd ai-assistant
python scripts/train_model.py
```

This script will:
1. Generate synthetic training data (~800 examples)
2. Train multiple ML models (Random Forest, Logistic Regression, SVM)
3. Evaluate all methods (ML, rule-based, LLM)
4. Save models to `models/` directory
5. Generate evaluation reports in `evaluation_results/`

## Use the Trained Model

The system automatically uses the ML model if available. The `classify_intent()` function now supports:

```python
# Auto mode (recommended): tries ML -> rule -> LLM
intent = await classify_intent(text, method="auto")

# ML only (fast, local)
intent = classify_intent(text, method="ml")  # Synchronous

# Rule-based only (fast, simple)
intent = classify_intent(text, method="rule")

# LLM only (accurate, API-based)
intent = await classify_intent(text, method="llm")
```

## Check Model Performance

After training, check the evaluation results:

```bash
cat evaluation_results/comparison_report.txt
```

Or view the confusion matrices:
- `evaluation_results/confusion_matrix_ml.png`
- `evaluation_results/confusion_matrix_rule.png`
- `evaluation_results/confusion_matrix_llm.png`

## Expected Results

Typical performance on synthetic data:
- **ML Model (Random Forest)**: ~85-95% accuracy
- **Rule-based**: ~60-70% accuracy
- **LLM API**: ~90-95% accuracy (but slower and costs money)

The ML model provides the best balance of **speed, cost, and accuracy**.

## Next Steps

1. **Improve Training Data**: Add more real examples to `backend/data/training/`
2. **Fine-tune Models**: Experiment with hyperparameters in `trainer.py`
3. **Add More Features**: Extend feature extraction in `feature_extractor.py`
4. **Monitor Performance**: Use the model registry to track versions

For more details, see [ML_README.md](ML_README.md)


