"""
Regression evaluation metrics used during training and exposed to the
Model Insights dashboard. This formalizes the metrics the original
attached script printed to the console (MAE, R^2) and adds RMSE, as
the project spec requires.
"""

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def evaluate_predictions(y_true, y_pred):
    """Return R^2, MAE and RMSE for a set of predictions as plain floats."""
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))

    return {
        "r2": float(r2),
        "mae": float(mae),
        "rmse": rmse,
    }
