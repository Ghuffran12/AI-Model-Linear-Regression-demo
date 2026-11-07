"""
Load the trained Linear Regression model and generate live property
price predictions for the Flask application.

This is the direct successor of section 4 of the attached Colab
script ("PREDICT HOUSE VALUE FOR ANY SIZE" / `predict_house_price`).
The same idea — build a one-row DataFrame with the right column names
and call `model.predict(...)` on it — is kept exactly, but it now
loads a persisted model via Joblib instead of relying on an in-memory
`model` variable, and supports the Location feature.

No hardcoded prices or random values are used here: every number
returned comes from `model.predict(...)` on the actual trained model.
"""

import json
import os
import sys

import joblib
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import config
from ml.data_preprocessing import build_feature_matrix

_model = None
_metadata = None


class ModelNotTrainedError(RuntimeError):
    """Raised when a prediction is requested before a model has been trained."""


def _ensure_loaded():
    global _model, _metadata
    if _model is not None and _metadata is not None:
        return

    if not os.path.exists(config.MODEL_PATH) or not os.path.exists(config.METADATA_PATH):
        raise ModelNotTrainedError(
            "No trained model was found. Run `python ml/train_model.py` first."
        )

    _model = joblib.load(config.MODEL_PATH)
    with open(config.METADATA_PATH) as f:
        _metadata = json.load(f)


def reload_model():
    """Force the next call to re-read the model and metadata from disk."""
    global _model, _metadata
    _model, _metadata = None, None
    _ensure_loaded()


def get_metadata():
    _ensure_loaded()
    return _metadata


def get_supported_locations():
    _ensure_loaded()
    return _metadata["locations"]


def predict_price(area_sqyd, location=None):
    """
    Predict a property price for a plot area in square yards and an
    optional locality. Returns a float amount in the configured
    currency. This is the single function every prediction in the
    application — API route, sample-size list, tests — goes through.
    """
    _ensure_loaded()

    row = pd.DataFrame(
        {
            "Plot_Area_SqYards": [float(area_sqyd)],
            "Location": [location if location else config.LOCATIONS[0]],
        }
    )

    X = build_feature_matrix(row)
    # Guard against any column-order drift between training and here.
    X = X[_metadata["feature_columns"]]

    predicted = _model.predict(X)[0]
    # A linear model is not mathematically guaranteed to stay positive
    # for every input combination; floor at 0 so the API can never
    # return a nonsensical negative price.
    return float(max(predicted, 0.0))


def predict_for_sizes(sizes, location=None):
    """Convenience helper: predict prices for a list of plot sizes."""
    return [{"area_sqyd": float(s), "predicted_price": predict_price(s, location)} for s in sizes]
