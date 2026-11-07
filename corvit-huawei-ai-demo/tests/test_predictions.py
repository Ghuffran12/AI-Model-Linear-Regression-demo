"""
Tests for the ML pipeline (ml/train_model.py, ml/predict.py) — the
project spec's core modelling requirements (section 13): the model
trains successfully, the saved model loads successfully, valid plot
sizes generate predictions, different inputs are processed
independently, and the supported prediction boundaries are enforced.
"""

import math
import os

import joblib
import pytest
from sklearn.linear_model import LinearRegression

from config import config
from ml import predict as ml_predict
from ml.train_model import train
from utils.validators import ValidationError, validate_prediction_range


@pytest.fixture(scope="module", autouse=True)
def trained_model():
    """
    Train once for this module and make sure ml.predict reloads that
    exact model afterwards, so every test below runs against a known,
    freshly-trained model rather than whatever was left on disk.
    """
    train()
    ml_predict.reload_model()
    yield
    ml_predict.reload_model()


# ---------------------------------------------------------------------
# "The model trains successfully"
# ---------------------------------------------------------------------

def test_training_produces_model_and_metadata_files():
    assert os.path.exists(config.MODEL_PATH)
    assert os.path.exists(config.METADATA_PATH)
    assert os.path.exists(config.TEST_PREDICTIONS_PATH)


def test_training_returns_a_fitted_linear_regression():
    model, metadata = train()
    assert isinstance(model, LinearRegression)
    assert hasattr(model, "coef_")
    assert metadata["model_type"] == "LinearRegression"


def test_training_metrics_are_finite_and_reasonable():
    _, metadata = train()
    for split in ("train_metrics", "test_metrics"):
        r2 = metadata[split]["r2"]
        mae = metadata[split]["mae"]
        rmse = metadata[split]["rmse"]
        assert math.isfinite(r2)
        assert math.isfinite(mae) and mae >= 0
        assert math.isfinite(rmse) and rmse >= 0
        # A sane fit on this synthetic, mostly-linear dataset should
        # explain most of the variance without being a suspicious 1.0.
        assert 0.5 < r2 <= 1.0


def test_training_record_counts_are_consistent():
    _, metadata = train()
    assert metadata["training_records"] + metadata["testing_records"] == metadata["total_records"]
    assert metadata["total_records"] > 0


# ---------------------------------------------------------------------
# "The saved model loads successfully"
# ---------------------------------------------------------------------

def test_saved_model_loads_with_joblib():
    loaded = joblib.load(config.MODEL_PATH)
    assert isinstance(loaded, LinearRegression)


def test_predict_module_loads_metadata_successfully():
    metadata = ml_predict.get_metadata()
    assert "feature_columns" in metadata
    assert "coefficients" in metadata
    assert metadata["feature_columns"] == list(metadata["coefficients"].keys())


def test_get_supported_locations_matches_config():
    assert ml_predict.get_supported_locations() == config.LOCATIONS


# ---------------------------------------------------------------------
# "Valid plot sizes generate predictions"
# ---------------------------------------------------------------------

@pytest.mark.parametrize("area", [120, 200, 500, 1200, 5000, 10000])
def test_valid_plot_sizes_generate_a_prediction(area):
    price = ml_predict.predict_price(area)
    assert math.isfinite(price)
    assert price > 0


@pytest.mark.parametrize("location", config.LOCATIONS)
def test_every_supported_locality_generates_a_prediction(location):
    price = ml_predict.predict_price(1000, location)
    assert math.isfinite(price)
    assert price > 0


def test_predict_without_a_locality_uses_the_baseline():
    price_default = ml_predict.predict_price(1000, None)
    price_baseline = ml_predict.predict_price(1000, config.LOCATIONS[0])
    assert price_default == pytest.approx(price_baseline)


# ---------------------------------------------------------------------
# "Different valid inputs are processed independently"
# ---------------------------------------------------------------------

def test_different_areas_give_different_prices():
    price_small = ml_predict.predict_price(200, "Askari")
    price_large = ml_predict.predict_price(5000, "Askari")
    assert price_large > price_small  # larger plot, same locality -> worth more


def test_different_localities_give_different_prices_for_the_same_area():
    prices = {loc: ml_predict.predict_price(800, loc) for loc in config.LOCATIONS}
    # Not every locality needs a unique price, but they can't all collapse
    # to a single value -- that would mean locality is silently ignored.
    assert len(set(round(p, 2) for p in prices.values())) > 1


def test_repeated_calls_do_not_interfere_with_each_other():
    # Guards against any shared/global-state bug between back-to-back
    # predictions for unrelated inputs.
    first = ml_predict.predict_price(300, "Clifton")
    ml_predict.predict_price(9000, "Gulshan-e-Iqbal")
    first_again = ml_predict.predict_price(300, "Clifton")
    assert first == pytest.approx(first_again)


def test_predict_for_sizes_matches_individual_predictions():
    sizes = [120, 500, 2000]
    batch = ml_predict.predict_for_sizes(sizes, "Bahria Town")
    for item, size in zip(batch, sizes):
        assert item["area_sqyd"] == pytest.approx(size)
        assert item["predicted_price"] == pytest.approx(ml_predict.predict_price(size, "Bahria Town"))


# ---------------------------------------------------------------------
# "The supported prediction boundaries are enforced"
# ---------------------------------------------------------------------

@pytest.mark.parametrize("area", [119, 50, 0.5])
def test_areas_below_minimum_are_rejected(area):
    with pytest.raises(ValidationError):
        validate_prediction_range(area)


@pytest.mark.parametrize("area", [10001, 25000])
def test_areas_above_maximum_are_rejected(area):
    with pytest.raises(ValidationError):
        validate_prediction_range(area)


def test_boundary_values_are_accepted():
    # Inclusive range: exactly 120 and exactly 10,000 must both work.
    validate_prediction_range(120)
    validate_prediction_range(10000)
    assert ml_predict.predict_price(120) > 0
    assert ml_predict.predict_price(10000) > 0


def test_model_not_trained_error_when_artifacts_are_absent(tmp_path, monkeypatch):
    """
    Point the predictor at a location with no model/metadata files and
    confirm it fails with a clear, specific error rather than crashing
    or silently falling back to something else.
    """
    monkeypatch.setattr(config, "MODEL_PATH", str(tmp_path / "missing_model.joblib"))
    monkeypatch.setattr(config, "METADATA_PATH", str(tmp_path / "missing_metadata.json"))
    try:
        with pytest.raises(ml_predict.ModelNotTrainedError):
            ml_predict.reload_model()
    finally:
        # Restore the real paths immediately and reload the genuine
        # trained model, so later tests never see this test's fallout.
        monkeypatch.undo()
        ml_predict.reload_model()
