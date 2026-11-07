"""
Tests for app.py — the project spec's "Flask routes return the expected
responses" and "the frontend communicates correctly with the backend"
requirements (section 13).

Request payloads deliberately mirror what static/js/predictor.js
actually sends: HTML form values arrive as JSON STRINGS (e.g. "500",
not 500), since that's what `inputElement.value` is in JavaScript.
"""

import json
import math

import pytest

from app import create_app
from config import config


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


# ---------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------

@pytest.mark.parametrize(
    "path",
    ["/", "/predictor", "/insights", "/how-it-works", "/about"],
)
def test_pages_return_200_and_html(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.content_type.startswith("text/html")


def test_home_page_contains_project_name(client):
    response = client.get("/")
    assert b"Corvit" in response.data
    assert b"Huawei" in response.data


def test_predictor_page_prefills_quick_select_size_from_query_string(client):
    response = client.get("/predictor?size=500")
    assert response.status_code == 200
    assert b'value="500"' in response.data


def test_unknown_page_returns_custom_404(client):
    response = client.get("/this-page-does-not-exist")
    assert response.status_code == 404
    assert b"404" in response.data


def test_unknown_api_route_returns_json_404(client):
    response = client.get("/api/this-does-not-exist")
    assert response.status_code == 404
    assert response.content_type.startswith("application/json")
    body = response.get_json()
    assert body["success"] is False


# ---------------------------------------------------------------------
# POST /api/predict — area mode
# ---------------------------------------------------------------------

def test_predict_area_mode_valid_request(client):
    # Values sent as strings, exactly like predictor.js's form payload.
    response = client.post(
        "/api/predict",
        json={"area": "500", "unit": "sqyd", "location": config.LOCATIONS[2]},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True

    data = body["data"]
    assert data["input"]["area"]["sqyd"] == pytest.approx(500.0)
    assert data["input"]["dimensions"]["estimated"] is True
    assert data["input"]["location"] == config.LOCATIONS[2]

    prediction = data["prediction"]
    assert prediction["predicted_price"] > 0
    assert prediction["currency"] == config.CURRENCY_CODE
    assert "PKR" in prediction["predicted_price_formatted"] or config.CURRENCY_CODE in prediction["predicted_price_formatted"]
    for key in ("price_per_sqyd", "price_per_sqft", "price_per_acre", "price_in_crore"):
        assert math.isfinite(prediction[key])
    assert "disclaimer" in data and len(data["disclaimer"]) > 0


def test_predict_area_mode_converts_other_units_before_predicting(client):
    # 4,500 sq ft == 500 sq yd — must land in range and match the sq-yd prediction.
    response_sqft = client.post("/api/predict", json={"area": "4500", "unit": "sqft"})
    response_sqyd = client.post("/api/predict", json={"area": "500", "unit": "sqyd"})
    assert response_sqft.status_code == response_sqyd.status_code == 200
    price_sqft = response_sqft.get_json()["data"]["prediction"]["predicted_price"]
    price_sqyd = response_sqyd.get_json()["data"]["prediction"]["predicted_price"]
    assert price_sqft == pytest.approx(price_sqyd, rel=1e-6)


def test_predict_without_locality_uses_default(client):
    response = client.post("/api/predict", json={"area": "1000", "unit": "sqyd"})
    assert response.status_code == 200
    assert response.get_json()["success"] is True


# ---------------------------------------------------------------------
# POST /api/predict — dimensions mode
# ---------------------------------------------------------------------

def test_predict_dimensions_mode_valid_request(client):
    response = client.post(
        "/api/predict",
        json={"length": "50", "breadth": "10", "unit": "sqyd"},
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["input"]["area"]["sqyd"] == pytest.approx(500.0)
    assert data["input"]["dimensions"]["estimated"] is False
    assert data["input"]["dimensions"]["length_sqyd"] == pytest.approx(50.0)
    assert data["input"]["dimensions"]["breadth_sqyd"] == pytest.approx(10.0)


def test_predict_dimensions_mode_matches_spec_worked_example(client):
    # "If the customer enters a length of 40 yards and a breadth of 30
    # yards ... Area = 40 x 30 = 1,200 square yards."
    response = client.post("/api/predict", json={"length": "40", "breadth": "30", "unit": "sqyd"})
    assert response.status_code == 200
    assert response.get_json()["data"]["input"]["area"]["sqyd"] == pytest.approx(1200.0)


def test_predict_rejects_inconsistent_area_and_dimensions(client):
    response = client.post(
        "/api/predict",
        json={"length": "40", "breadth": "30", "area": "5000", "unit": "sqyd"},
    )
    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_predict_accepts_consistent_area_and_dimensions(client):
    response = client.post(
        "/api/predict",
        json={"length": "40", "breadth": "30", "area": "1200", "unit": "sqyd"},
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["input"]["dimensions"]["estimated"] is False


# ---------------------------------------------------------------------
# POST /api/predict — validation and the prediction-range boundary
# ---------------------------------------------------------------------

def test_predict_rejects_empty_payload(client):
    response = client.post("/api/predict", json={})
    assert response.status_code == 400
    assert "area" in response.get_json()["error"].lower() or "length" in response.get_json()["error"].lower()


def test_predict_rejects_below_minimum_range(client):
    response = client.post("/api/predict", json={"area": "50", "unit": "sqyd"})
    assert response.status_code == 400
    assert "Prediction Not Available" in response.get_json()["error"]


def test_predict_rejects_above_maximum_range(client):
    response = client.post("/api/predict", json={"area": "15000", "unit": "sqyd"})
    assert response.status_code == 400
    assert "Prediction Not Available" in response.get_json()["error"]


def test_predict_does_not_bypass_range_via_acres(client):
    # 3 acres ~= 14,520 sq yd -- well outside the supported range. Unit
    # conversion must not be a loophole around the prediction limit.
    response = client.post("/api/predict", json={"area": "3", "unit": "acre"})
    assert response.status_code == 400
    assert "Prediction Not Available" in response.get_json()["error"]


def test_predict_rejects_negative_dimensions(client):
    response = client.post("/api/predict", json={"length": "-10", "breadth": "5", "unit": "sqyd"})
    assert response.status_code == 400


def test_predict_rejects_alphabetic_input(client):
    response = client.post("/api/predict", json={"area": "five hundred", "unit": "sqyd"})
    assert response.status_code == 400


def test_predict_rejects_invalid_unit(client):
    response = client.post("/api/predict", json={"area": "500", "unit": "furlong"})
    assert response.status_code == 400


def test_predict_rejects_invalid_locality(client):
    response = client.post(
        "/api/predict", json={"area": "500", "unit": "sqyd", "location": "Nowhereville"}
    )
    assert response.status_code == 400


def test_predict_rejects_non_finite_values(client):
    # Sent as a raw body so the literal NaN token survives JSON parsing
    # (Flask's json=... helper would reject it before it ever reaches
    # the view, which wouldn't actually exercise the validator).
    response = client.post(
        "/api/predict",
        data=json.dumps({"area": float("nan"), "unit": "sqyd"}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_predict_handles_malformed_json_without_500(client):
    response = client.post("/api/predict", data="not valid json", content_type="application/json")
    assert response.status_code == 400
    assert response.get_json()["success"] is False


# ---------------------------------------------------------------------
# POST /api/convert
# ---------------------------------------------------------------------

def test_convert_area_mode(client):
    response = client.post("/api/convert", json={"area": "1200", "unit": "sqyd"})
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["area"]["sqft"] == pytest.approx(10800.0)  # 1,200 x 9


def test_convert_dimensions_mode(client):
    response = client.post("/api/convert", json={"length": "40", "breadth": "30", "unit": "sqyd"})
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["area"]["sqyd"] == pytest.approx(1200.0)


def test_convert_allows_areas_outside_prediction_range(client):
    # Conversion must keep working for big acreages; only /api/predict
    # enforces the 120-10,000 sq yd limit.
    response = client.post("/api/convert", json={"area": "5", "unit": "acre"})
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["within_prediction_range"] is False
    assert data["area"]["sqyd"] == pytest.approx(5 * config.SQYD_PER_ACRE)


# ---------------------------------------------------------------------
# GET /api/model-info, /api/dataset-stats, /api/sample-predictions,
# /api/test-predictions
# ---------------------------------------------------------------------

def test_model_info(client):
    response = client.get("/api/model-info")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["model_type"] == "LinearRegression"
    assert "test_metrics" in data and "r2" in data["test_metrics"]


def test_dataset_stats(client):
    response = client.get("/api/dataset-stats")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["total_records"] > 0
    assert set(data["locations"]) <= set(config.LOCATIONS)
    assert data["is_synthetic"] is True


def test_sample_predictions_covers_every_quick_select_size(client):
    response = client.get("/api/sample-predictions")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) == len(config.QUICK_SELECT_SIZES)
    sizes_returned = {item["area_sqyd"] for item in data}
    assert sizes_returned == set(float(s) for s in config.QUICK_SELECT_SIZES)


def test_sample_predictions_rejects_invalid_locality(client):
    response = client.get("/api/sample-predictions?location=Nowhereville")
    assert response.status_code == 400


def test_test_predictions_available_for_insights_chart(client):
    response = client.get("/api/test-predictions")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) > 0
    assert {"area_sqyd", "actual_price", "predicted_price"} <= set(data[0].keys())
