"""
Corvit Huawei AI Demo — central configuration.

Every tunable value used across the ML pipeline, the Flask backend and
the frontend (currency, the supported prediction range, quick-select
sizes, unit-conversion constants and file locations) lives here so it
only ever needs to change in one place.

Values can be overridden with environment variables (see .env.example)
without touching any code.
"""

import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _env_float(name, default):
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


class Config:
    # ------------------------------------------------------------------
    # Flask
    # ------------------------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.environ.get("FLASK_DEBUG", "True").strip().lower() in ("1", "true", "yes")

    # ------------------------------------------------------------------
    # Currency (configurable; PKR is the default per project requirements)
    # ------------------------------------------------------------------
    CURRENCY_CODE = os.environ.get("CURRENCY_CODE", "PKR")
    CURRENCY_SYMBOL = os.environ.get("CURRENCY_SYMBOL", "PKR")

    # ------------------------------------------------------------------
    # Supported LIVE PREDICTION range, in square yards.
    # Unit conversion (e.g. acres) is allowed outside this range;
    # the *prediction* endpoint enforces it regardless of input unit.
    # ------------------------------------------------------------------
    MIN_PREDICTION_SQYD = _env_float("MIN_PREDICTION_SQYD", 120)
    MAX_PREDICTION_SQYD = _env_float("MAX_PREDICTION_SQYD", 10000)

    # Quick-select plot sizes shown as buttons (square yards)
    QUICK_SELECT_SIZES = [120, 200, 240, 400, 420, 450, 500, 700, 800, 1000, 1200, 2000, 4000, 5000]

    # Sample localities supported by the demonstration dataset.
    # NOTE: "Askari" is listed first deliberately — it is the baseline
    # locality absorbed into the model's intercept during one-hot
    # encoding (see ml/data_preprocessing.py), which keeps the learned
    # per-locality coefficients directly interpretable.
    LOCATIONS = [
        "Askari",
        "DHA Phase 6",
        "Bahria Town",
        "Gulshan-e-Iqbal",
        "Clifton",
    ]

    # ------------------------------------------------------------------
    # Unit conversion constants (documented, per project spec)
    # ------------------------------------------------------------------
    SQFT_PER_SQYD = 9.0
    SQM_PER_SQYD = 0.836127
    SQYD_PER_ACRE = 4840.0
    SQFT_PER_ACRE = 43560.0

    # ------------------------------------------------------------------
    # File locations
    # ------------------------------------------------------------------
    DATA_DIR = os.path.join(BASE_DIR, "data")
    DATASET_PATH = os.path.join(DATA_DIR, "property_data.csv")

    MODELS_DIR = os.path.join(BASE_DIR, "models")
    MODEL_PATH = os.path.join(MODELS_DIR, "linear_regression_model.joblib")
    METADATA_PATH = os.path.join(MODELS_DIR, "model_metadata.json")
    TEST_PREDICTIONS_PATH = os.path.join(MODELS_DIR, "test_predictions.json")

    # ------------------------------------------------------------------
    # Dataset generation
    # ------------------------------------------------------------------
    RANDOM_SEED = 42
    N_SAMPLES = int(os.environ.get("N_SAMPLES", 600))


config = Config()
