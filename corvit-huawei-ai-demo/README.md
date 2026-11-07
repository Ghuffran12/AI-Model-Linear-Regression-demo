# Corvit Huawei AI Demo

An educational, fully-working AI property price prediction web application.
A customer enters a plot's size (directly, or via length & breadth, in
square yards/feet/meters/acres) and an optional locality, and a genuine
**Scikit-learn Linear Regression** model — trained on a documented
synthetic dataset — returns a live price estimate, with price-per-unit
figures, model-performance metrics and interactive charts alongside it.

> **This is a machine-learning demonstration.** All prices are generated
> by a model trained on clearly-labelled **synthetic** data. They are
> not verified real-estate valuations and must not be used for actual
> buying, selling or investment decisions. This project is not an
> official product of, or endorsed by, Huawei or Corvit.

---

## 1. Technology stack

| Layer              | Technology                                                   |
|---------------------|----------------------------------------------------------------|
| ML model             | `scikit-learn` — `LinearRegression`                           |
| Data processing       | `pandas`, `numpy`                                              |
| Model persistence     | `joblib`                                                       |
| Backend / API         | `Flask`                                                         |
| Frontend               | Server-rendered HTML5, hand-written CSS3 (no framework), vanilla JS |
| Charts                  | `Chart.js` (via CDN)                                            |
| Testing                 | `pytest`                                                        |

## 2. Project / folder structure

```text
corvit-huawei-ai-demo/
├── app.py                      # Flask app factory, page routes, JSON API
├── config.py                   # Every tunable value lives here (currency, range, localities, paths...)
├── requirements.txt
├── README.md                   # You are here
├── .gitignore
├── .env.example                # Optional overrides -- copy to .env
│
├── data/
│   ├── property_data.csv       # Synthetic training dataset (generated)
│   └── README.md                # Dataset columns + documented generation assumptions
│
├── models/
│   ├── linear_regression_model.joblib   # Trained model (generated)
│   ├── model_metadata.json              # Coefficients, metrics, feature columns (generated)
│   └── test_predictions.json            # Held-out actual vs. predicted pairs, for the Insights chart (generated)
│
├── ml/                           # Machine-learning pipeline (see section 5 below)
│   ├── generate_dataset.py       # Synthetic data generation
│   ├── data_preprocessing.py     # Load / clean / validate / feature-engineer / split
│   ├── train_model.py            # Train, evaluate, persist (run this to (re)train)
│   ├── evaluate_model.py         # R^2 / MAE / RMSE
│   └── predict.py                # Load the saved model and generate live predictions
│
├── utils/
│   ├── area_converter.py         # sq yd / sq ft / sq m / acre conversions + dimension math
│   ├── validators.py             # Input validation, incl. the 120-10,000 sq yd range
│   └── price_formatter.py        # PKR / crore / lakh formatting
│
├── templates/                    # Jinja2 templates (base.html + 6 pages + icons/)
├── static/
│   ├── css/                      # style.css (theme) + responsive.css (breakpoints)
│   └── js/                       # main.js, predictor.js, charts.js
│
├── tests/                        # pytest suite -- see section 7
│
└── reference/
    └── original_colab_script.py  # The attached script, kept verbatim for comparison -- see section 11
```

## 3. Python version

Developed and tested with **Python 3.13**. Python 3.10+ should work fine.

## 4. Setup

### 4.1 Create and activate a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4.2 Install dependencies

```bash
pip install -r requirements.txt
```

### 4.3 (Optional) configure environment variables

The app runs with no extra setup — `config.py` has sensible built-in
defaults. If you want to override currency, the prediction range, the
dataset size, or the Flask secret key, copy `.env.example` to `.env` and
edit it:

```bash
cp .env.example .env     # Windows: copy .env.example .env
```

## 5. Dataset and model training

A dataset and trained model are **already included** in this delivery
(`data/property_data.csv`, `models/linear_regression_model.joblib`), so
you can run the app immediately. To regenerate them from scratch (e.g.
after changing `config.py`, or to get a fresh random sample):

```bash
python ml/generate_dataset.py   # (re)generate data/property_data.csv
python ml/train_model.py        # train, evaluate, and save the model + metadata
```

`train_model.py` will also generate the dataset itself automatically if
`data/property_data.csv` doesn't exist — and `app.py` will run the
entire pipeline (generate data, if needed, then train) automatically on
first startup if `models/` is empty, so the app can never fail to start
just because nothing has been trained yet.

Training prints a summary like this:

```
========== MODEL TRAINING COMPLETE ==========
Training records: 480
Testing records:  120

Learned Linear Regression Formula:
Property_Price = -2,070,161.87 + (150,034.15 x Plot_Area_SqYards) + (16,715,254.98 x Loc_DHA Phase 6) + (10,900,119.85 x Loc_Bahria Town) + (-1,112,070.07 x Loc_Gulshan-e-Iqbal) + (25,178,727.86 x Loc_Clifton)

Test R^2:   0.9989
Test MAE:   PKR 8,227,148
Test RMSE:  PKR 10,247,775
```

(Exact figures above are from an actual run with `random_state=42` and
are fully reproducible — delete `data/property_data.csv` and
`models/` and re-run the two commands above to regenerate them from
scratch and get the identical numbers back.)

See **`data/README.md`** for exactly how the synthetic prices were
generated (documented assumptions, not invented real-market figures),
and the Model Insights page in the running app for the live version of
the same numbers.

## 6. Running the application

```bash
python app.py
```

Then open **http://127.0.0.1:5000** in a browser. Stop the server with
`Ctrl+C`.

### Using the website

- **Home** — overview, live model stats, and quick plot-size shortcuts.
- **AI Price Predictor** — enter a plot area (or length & breadth),
  pick a unit and an optional locality, and click **Predict property
  price** for a live estimate, a size-vs-price chart, and a comparison
  against the predefined quick-select sizes.
- **Model Insights** — the model's R², MAE and RMSE, its learned
  formula, an actual-vs-predicted chart on held-out test data, and
  dataset statistics by locality.
- **How It Works** — a plain-language walkthrough of the five steps
  behind every prediction.
- **About** — what this demo is (and isn't), and the full disclaimer.

Every number shown is computed live by the backend from the actual
trained model — nothing in the UI is a hardcoded or random placeholder.

## 7. Running the automated tests

```bash
python -m pytest tests/ -v
```

150 tests across four files, all currently passing:

- `tests/test_area_converter.py` — unit-conversion correctness (incl.
  the spec's own 40×30 yd = 1,200 sq yd worked example) and
  length × breadth area math.
- `tests/test_validators.py` — rejection of empty / negative / zero /
  non-numeric / NaN / infinite values, invalid units, invalid
  localities, inconsistent dimensions, and the exact "Prediction Not
  Available" boundary message.
- `tests/test_predictions.py` — the model trains successfully, the
  saved model loads successfully, valid sizes across every locality
  generate predictions, different inputs are processed independently,
  and the 120–10,000 sq yd boundary is enforced.
- `tests/test_routes.py` — every page returns 200, the custom 404 page
  works, and every JSON API endpoint (`/api/predict`, `/api/convert`,
  `/api/model-info`, `/api/dataset-stats`, `/api/sample-predictions`,
  `/api/test-predictions`) behaves exactly as `static/js/predictor.js`
  and `charts.js` expect — including sending values as strings, the way
  real HTML form inputs do.

## 8. Configuring currency and the prediction range

Everything is centralised in **`config.py`**:

```python
CURRENCY_CODE = os.environ.get("CURRENCY_CODE", "PKR")
MIN_PREDICTION_SQYD = _env_float("MIN_PREDICTION_SQYD", 120)
MAX_PREDICTION_SQYD = _env_float("MAX_PREDICTION_SQYD", 10000)
QUICK_SELECT_SIZES = [120, 200, 240, 400, 420, 450, 500, 700, 800, 1000, 1200, 2000, 4000, 5000]
LOCATIONS = ["Askari", "DHA Phase 6", "Bahria Town", "Gulshan-e-Iqbal", "Clifton"]
```

Change any of these directly, or override `CURRENCY_CODE`,
`MIN_PREDICTION_SQYD` and `MAX_PREDICTION_SQYD` via environment
variables / `.env` without touching code (see `.env.example`). If you
change the prediction range or add/remove localities, **re-run
`python ml/train_model.py`** afterwards so the model, its saved
coefficients and `models/model_metadata.json` stay in sync with the new
configuration.

## 9. Replacing the demonstration dataset with real data

See the "Regenerating or replacing this dataset" section of
**`data/README.md`** for the full steps. In short: swap in your own CSV
with the same columns, update `config.LOCATIONS` if your localities
differ, re-run `python ml/train_model.py`, and update the synthetic-data
disclaimers in `templates/about.html`, `templates/base.html` and
`app.py`'s `/api/predict` response, since they currently (correctly)
state that the data is synthetic.

## 10. Design notes worth knowing

- **Why only two model features (area + locality), not area + length +
  breadth together:** `Length x Breadth = Area`, so including all three
  would be redundant and create unnecessary multicollinearity, which
  the project spec explicitly warns against. Length and breadth are
  still fully supported in the UI and dataset for display, the
  dimensions calculator, and consistency validation — they're just not
  fed into the regression a second time alongside the area they
  already determine. See the docstring at the top of
  `ml/data_preprocessing.py`.
- **Unit conversion is always a pivot through square yards** (the
  model's native unit), both for the live prediction and the
  standalone converter — see `utils/area_converter.py`. Entering a size
  in acres cannot be used to sneak past the 120–10,000 sq yd prediction
  limit: `/api/convert` will happily show you the conversion, but
  `/api/predict` always re-checks the canonical square-yard value.
- **Estimated vs. actual dimensions are always labelled.** If you only
  enter an area, the app estimates a plausible length/breadth (default
  1:1, or your own ratio) purely for display — the predicted price
  never depends on that estimate, and the UI/API response always marks
  it `"estimated": true`.
- **The backend is authoritative.** `predictor.js` mirrors the unit-
  and area-math client-side purely for instant feedback as you type;
  every actual prediction and every number shown in a result card comes
  from the Flask `/api/predict` response, not from JavaScript.

## 11. Provenance: the originally-attached Linear Regression script

This project was built around a user-supplied Google Colab script
(single-feature `House_Size_SqYards -> House_Price_PKR`, trained with
`sklearn.linear_model.LinearRegression`, `train_test_split(test_size=0.20,
random_state=42)`, evaluated with MAE/R², predicted via a one-row
DataFrame). The original file is kept, byte-for-byte unmodified, at
**`reference/original_colab_script.py`** for direct comparison — it is
never imported or run by the application itself. Its logic lives on,
reorganised and extended, across:

- **`ml/generate_dataset.py`** — descendant of the script's "GENERATE
  100 HOUSE RECORDS" section: same base-price + per-unit-rate + noise
  idea, extended to the full 120–10,000 sq yd range and a `Location`
  feature.
- **`ml/data_preprocessing.py`** — the load/clean/split step the
  original script did inline, pulled into its own module and given
  real validation.
- **`ml/train_model.py`** — the same `train_test_split(..., test_size=0.20,
  random_state=42)` and `LinearRegression().fit(...)` calls, now
  persisting the model, its metadata and its test-set predictions.
- **`ml/predict.py`** — the same "build a one-row DataFrame, call
  `model.predict(...)`" approach from the script's
  `predict_house_price` function, now loading a persisted model via
  Joblib instead of an in-memory variable, and serving the live Flask
  API instead of `ipywidgets`.

No hardcoded prices, random placeholders or frontend-only formulas are
used anywhere — every number shown is the real model's output.
