
import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, jsonify, render_template, request

from config import config
from ml import predict as ml_predict
from ml.train_model import train as train_model
from utils import area_converter, price_formatter, validators


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    # The project spec requires the app to be able to produce its own
    # trained model automatically if one isn't already present, so it
    # never fails to start just because `models/` is empty.
    if not (os.path.exists(config.MODEL_PATH) and os.path.exists(config.METADATA_PATH)):
        print("No trained model found - training a new Linear Regression model...")
        train_model()

    @app.context_processor
    def inject_globals():
        return {
            "site_name": "Corvit Huawei AI Demo",
            "current_year": datetime.now().year,
            "quick_sizes": config.QUICK_SELECT_SIZES,
            "min_sqyd": config.MIN_PREDICTION_SQYD,
            "max_sqyd": config.MAX_PREDICTION_SQYD,
            "currency_code": config.CURRENCY_CODE,
        }

    @app.template_filter("commas")
    def commas_filter(value):
        try:
            return f"{float(value):,.0f}"
        except (TypeError, ValueError):
            return value

    # ------------------------------------------------------------------
    # Page routes
    # ------------------------------------------------------------------

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/predictor")
    def predictor_page():
        try:
            metadata = ml_predict.get_metadata()
            locations = ml_predict.get_supported_locations()
        except ml_predict.ModelNotTrainedError:
            metadata, locations = None, config.LOCATIONS
        return render_template("predictor.html", locations=locations, metadata=metadata)

    @app.route("/insights")
    def insights_page():
        try:
            metadata = ml_predict.get_metadata()
        except ml_predict.ModelNotTrainedError:
            metadata = None
        return render_template("insights.html", metadata=metadata)

    @app.route("/how-it-works")
    def how_it_works_page():
        return render_template("how_it_works.html")

    @app.route("/about")
    def about_page():
        return render_template("about.html")

    # ------------------------------------------------------------------
    # JSON API routes
    # ------------------------------------------------------------------

    @app.route("/api/convert", methods=["POST"])
    def api_convert():
        payload = request.get_json(silent=True) or {}
        try:
            unit = validators.validate_unit(payload.get("unit", "sqyd"))
            has_dimensions = payload.get("length") not in (None, "") and payload.get("breadth") not in (None, "")

            if has_dimensions:
                length = validators.validate_positive_number(payload.get("length"), "Plot length")
                breadth = validators.validate_positive_number(payload.get("breadth"), "Plot breadth")
                area_in_unit = area_converter.area_from_dimensions(length, breadth)
                area_sqyd = area_converter.to_sqyd(area_in_unit, unit)
                result = {
                    "mode": "dimensions",
                    "length": length,
                    "breadth": breadth,
                    "unit": unit,
                    "area": area_converter.all_units(area_sqyd),
                }
            else:
                area = validators.validate_positive_number(payload.get("area"), "Plot area")
                area_sqyd = area_converter.to_sqyd(area, unit)
                ratio = payload.get("ratio", 1.0)
                try:
                    ratio = float(ratio) if ratio not in (None, "") else 1.0
                except (TypeError, ValueError):
                    ratio = 1.0
                dims = area_converter.estimate_dimensions_from_area(area_sqyd, ratio)
                result = {
                    "mode": "area",
                    "unit": unit,
                    "area": area_converter.all_units(area_sqyd),
                    "estimated_dimensions": dims,
                }

            result["within_prediction_range"] = (
                config.MIN_PREDICTION_SQYD <= area_sqyd <= config.MAX_PREDICTION_SQYD
            )
            return jsonify({"success": True, "data": result})

        except validators.ValidationError as e:
            return jsonify({"success": False, "error": str(e)}), 400
        except Exception:
            # Never leak internals to the client, but never go silent
            # server-side either -- log the real cause for debugging.
            app.logger.exception("Unexpected error in /api/convert")
            return jsonify({"success": False, "error": "Could not process the conversion request."}), 400

    @app.route("/api/predict", methods=["POST"])
    def api_predict():
        payload = request.get_json(silent=True) or {}
        try:
            unit = validators.validate_unit(payload.get("unit", "sqyd"))
            location = validators.validate_location(payload.get("location"))

            length_raw = payload.get("length")
            breadth_raw = payload.get("breadth")
            area_raw = payload.get("area")

            length_sqyd = breadth_sqyd = None
            has_dimensions = length_raw not in (None, "") and breadth_raw not in (None, "")
            if has_dimensions:
                length_val = validators.validate_positive_number(length_raw, "Plot length")
                breadth_val = validators.validate_positive_number(breadth_raw, "Plot breadth")
                length_sqyd = area_converter.to_sqyd(length_val, unit)
                breadth_sqyd = area_converter.to_sqyd(breadth_val, unit)

            has_area = area_raw not in (None, "")
            if has_area:
                area_val = validators.validate_positive_number(area_raw, "Plot area")
                area_sqyd = area_converter.to_sqyd(area_val, unit)
            elif has_dimensions:
                area_sqyd = area_converter.area_from_dimensions(length_sqyd, breadth_sqyd)
            else:
                raise validators.ValidationError("Please provide a plot area, or both length and breadth.")

            # Cross-check consistency only when BOTH were explicitly given.
            if has_area and has_dimensions:
                validators.validate_dimensions_consistency(length_sqyd, breadth_sqyd, area_sqyd)

            validators.validate_prediction_range(area_sqyd)

            if has_dimensions:
                dimensions = {
                    "length_sqyd": round(length_sqyd, 2),
                    "breadth_sqyd": round(breadth_sqyd, 2),
                    "estimated": False,
                }
            else:
                ratio = payload.get("ratio", 1.0)
                try:
                    ratio = float(ratio) if ratio not in (None, "") else 1.0
                except (TypeError, ValueError):
                    ratio = 1.0
                est = area_converter.estimate_dimensions_from_area(area_sqyd, ratio)
                dimensions = {"length_sqyd": est["length"], "breadth_sqyd": est["breadth"], "estimated": True}

            predicted_price = ml_predict.predict_price(area_sqyd, location)

            response = {
                "input": {
                    "area": area_converter.all_units(area_sqyd),
                    "dimensions": dimensions,
                    "unit": unit,
                    "location": location,
                },
                "prediction": {
                    "predicted_price": round(predicted_price, 2),
                    "predicted_price_formatted": price_formatter.format_currency(predicted_price),
                    "price_in_crore": round(price_formatter.to_crore(predicted_price), 3),
                    "price_per_sqyd": round(predicted_price / area_sqyd, 2),
                    "price_per_sqft": round(predicted_price / area_converter.sqyd_to_sqft(area_sqyd), 2),
                    "price_per_acre": round(predicted_price / area_converter.sqyd_to_acres(area_sqyd), 2),
                    "currency": config.CURRENCY_CODE,
                },
                "disclaimer": (
                    "This estimate is generated by a Linear Regression model trained on synthetic "
                    "demonstration data for the Corvit Huawei AI Demo. It is not a verified "
                    "real-estate market valuation."
                ),
            }
            return jsonify({"success": True, "data": response})

        except validators.ValidationError as e:
            return jsonify({"success": False, "error": str(e)}), 400
        except ml_predict.ModelNotTrainedError as e:
            return jsonify({"success": False, "error": str(e)}), 503
        except Exception:
            app.logger.exception("Unexpected error in /api/predict")
            return jsonify({"success": False, "error": "Could not process the prediction request."}), 400

    @app.route("/api/model-info")
    def api_model_info():
        try:
            return jsonify({"success": True, "data": ml_predict.get_metadata()})
        except ml_predict.ModelNotTrainedError as e:
            return jsonify({"success": False, "error": str(e)}), 503

    @app.route("/api/dataset-stats")
    def api_dataset_stats():
        try:
            import numpy as np
            import pandas as pd

            if not os.path.exists(config.DATASET_PATH):
                raise FileNotFoundError
            df = pd.read_csv(config.DATASET_PATH)

            counts, bin_edges = np.histogram(df["Property_Price"], bins=8)
            stats = {
                "total_records": int(len(df)),
                "min_area_sqyd": float(df["Plot_Area_SqYards"].min()),
                "max_area_sqyd": float(df["Plot_Area_SqYards"].max()),
                "min_price": float(df["Property_Price"].min()),
                "max_price": float(df["Property_Price"].max()),
                "avg_price": float(df["Property_Price"].mean()),
                "locations": sorted(df["Location"].unique().tolist()),
                "records_per_location": df["Location"].value_counts().to_dict(),
                "price_histogram": {
                    "bin_edges": [float(x) for x in bin_edges],
                    "counts": [int(x) for x in counts],
                },
                "is_synthetic": True,
            }
            return jsonify({"success": True, "data": stats})
        except FileNotFoundError:
            return jsonify({"success": False, "error": "Dataset not found."}), 503

    @app.route("/api/sample-predictions")
    def api_sample_predictions():
        try:
            location = request.args.get("location")
            location = validators.validate_location(location)
            results = ml_predict.predict_for_sizes(config.QUICK_SELECT_SIZES, location)
            for r in results:
                r["predicted_price_formatted"] = price_formatter.format_currency(r["predicted_price"])
            return jsonify({"success": True, "data": results})
        except validators.ValidationError as e:
            return jsonify({"success": False, "error": str(e)}), 400
        except ml_predict.ModelNotTrainedError as e:
            return jsonify({"success": False, "error": str(e)}), 503

    @app.route("/api/test-predictions")
    def api_test_predictions():
        import json

        if not os.path.exists(config.TEST_PREDICTIONS_PATH):
            return jsonify({"success": False, "error": "No evaluation data available yet."}), 503
        with open(config.TEST_PREDICTIONS_PATH) as f:
            data = json.load(f)
        return jsonify({"success": True, "data": data})

    # ------------------------------------------------------------------
    # Error handlers — never leak internal paths or tracebacks
    # ------------------------------------------------------------------

    @app.errorhandler(404)
    def not_found(_e):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "error": "Endpoint not found."}), 404
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(_e):
        return jsonify({"success": False, "error": "An internal server error occurred."}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=config.DEBUG)
