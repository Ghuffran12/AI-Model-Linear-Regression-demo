"""
Train the Linear Regression property-price model, evaluate it on a
held-out test set, and save the trained model + metadata with Joblib.

This module is the direct successor of sections 2-3 of the attached
Colab script ("PREPARE DATA FOR MACHINE LEARNING" / "TRAIN LINEAR
REGRESSION MODEL"): the same `train_test_split(..., test_size=0.20,
random_state=42)` and `LinearRegression().fit(...)` calls are used
here, now driven by the shared preprocessing pipeline and config, and
extended to persist the model, its metadata and its test-set
predictions so the rest of the application can use them.

Run directly:
    python ml/train_model.py
"""

import json
import os
import sys
from datetime import datetime, timezone

import joblib
from sklearn.linear_model import LinearRegression

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import config
from ml.data_preprocessing import prepare_training_data
from ml.evaluate_model import evaluate_predictions
from ml.generate_dataset import save_dataset


def train():
    """Run the full training pipeline and persist all resulting artifacts."""
    # Make sure a dataset exists; generate one if this is a first run,
    # so the application can always train itself from nothing.
    if not os.path.exists(config.DATASET_PATH):
        print("No dataset found - generating a new synthetic dataset...")
        save_dataset()

    data = prepare_training_data()
    X_train, X_test = data["X_train"], data["X_test"]
    y_train, y_test = data["y_train"], data["y_test"]

    model = LinearRegression()
    model.fit(X_train, y_train)

    train_predictions = model.predict(X_train)
    test_predictions = model.predict(X_test)

    train_metrics = evaluate_predictions(y_train, train_predictions)
    test_metrics = evaluate_predictions(y_test, test_predictions)

    os.makedirs(config.MODELS_DIR, exist_ok=True)
    joblib.dump(model, config.MODEL_PATH)

    metadata = {
        "model_type": "LinearRegression",
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "feature_columns": data["feature_columns"],
        "locations": config.LOCATIONS,
        "baseline_location": config.LOCATIONS[0],
        "intercept": float(model.intercept_),
        "coefficients": {
            col: float(coef) for col, coef in zip(data["feature_columns"], model.coef_)
        },
        "training_records": int(len(X_train)),
        "testing_records": int(len(X_test)),
        "total_records": int(len(X_train) + len(X_test)),
        "train_metrics": train_metrics,
        "test_metrics": test_metrics,
        "min_prediction_sqyd": config.MIN_PREDICTION_SQYD,
        "max_prediction_sqyd": config.MAX_PREDICTION_SQYD,
        "currency": config.CURRENCY_CODE,
        "random_state": config.RANDOM_SEED,
    }

    with open(config.METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    # Store (area, actual, predicted) for every test-set record so the
    # Model Insights page can draw a genuine actual-vs-predicted chart
    # from this exact run, not from invented numbers.
    test_points = [
        {
            "area_sqyd": float(area),
            "actual_price": float(actual),
            "predicted_price": float(pred),
        }
        for area, actual, pred in zip(X_test["Plot_Area_SqYards"], y_test, test_predictions)
    ]
    with open(config.TEST_PREDICTIONS_PATH, "w") as f:
        json.dump(test_points, f, indent=2)

    print("========== MODEL TRAINING COMPLETE ==========")
    print(f"Training records: {metadata['training_records']}")
    print(f"Testing records:  {metadata['testing_records']}")
    print(f"\nLearned Linear Regression Formula:")
    coef_str = " + ".join(f"({c:,.2f} x {name})" for name, c in metadata["coefficients"].items())
    print(f"Property_Price = {metadata['intercept']:,.2f} + {coef_str}")
    print(f"\nTest R^2:   {test_metrics['r2']:.4f}")
    print(f"Test MAE:   {config.CURRENCY_CODE} {test_metrics['mae']:,.0f}")
    print(f"Test RMSE:  {config.CURRENCY_CODE} {test_metrics['rmse']:,.0f}")
    print(f"\nModel saved to:    {config.MODEL_PATH}")
    print(f"Metadata saved to: {config.METADATA_PATH}")

    return model, metadata


if __name__ == "__main__":
    train()
