"""
Data loading, cleaning and feature preparation for the Linear
Regression property-price model.

This is the "validate/clean/prepare features/split" stage that the
original attached script did inline (steps 1-2 of its script). Here
it is pulled out into its own module, as the project spec requires,
and extended with real cleaning/validation instead of assuming the
generated data is already perfect.

Modeling choice (documented): the regression uses Plot_Area_SqYards
(continuous) and Location (one-hot encoded, first category dropped)
as its only features. Plot_Length_Yards and Plot_Breadth_Yards are
kept in the dataset and used for display/validation elsewhere in the
app, but are deliberately NOT fed into the regression alongside area,
since Length x Breadth = Area and including all three would create
unnecessary multicollinearity, as the project spec warns against.
"""

import os
import sys

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import config

REQUIRED_COLUMNS = [
    "Property_ID",
    "Plot_Area_SqYards",
    "Plot_Length_Yards",
    "Plot_Breadth_Yards",
    "Location",
    "Property_Price",
    "Currency",
]

TARGET_COLUMN = "Property_Price"


def load_dataset(path=None):
    """Load the property dataset from CSV and run basic structural checks."""
    path = path or config.DATASET_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Dataset not found at '{path}'. Run `python ml/generate_dataset.py` "
            "to create it before training."
        )

    df = pd.read_csv(path)

    missing_columns = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {missing_columns}")

    return df


def clean_dataset(df):
    """
    Remove rows with missing, non-numeric, non-finite or otherwise
    invalid values so the model is never trained on bad data.
    """
    df = df.copy()
    df = df.dropna(subset=REQUIRED_COLUMNS)

    numeric_cols = ["Plot_Area_SqYards", "Plot_Length_Yards", "Plot_Breadth_Yards", "Property_Price"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=numeric_cols)
    df = df[np.isfinite(df[numeric_cols].to_numpy()).all(axis=1)]

    df = df[
        (df["Plot_Area_SqYards"] > 0)
        & (df["Plot_Length_Yards"] > 0)
        & (df["Plot_Breadth_Yards"] > 0)
        & (df["Property_Price"] > 0)
    ]

    # Locations outside the supported list cannot be modelled (there is
    # no trained coefficient for them), so they are dropped here with a
    # clear explanation rather than silently mis-encoded.
    df = df[df["Location"].isin(config.LOCATIONS)]

    df = df.drop_duplicates(subset=["Property_ID"])
    return df.reset_index(drop=True)


def encode_locations(location_series):
    """
    One-hot encode a Location column against the FULL, FIXED set of
    config.LOCATIONS (not just whatever happens to be present in the
    rows passed in). This is essential for correctness: it guarantees
    the exact same dummy columns, in the exact same order, whether this
    is called on 600 training rows or on a single row at prediction
    time. The first category in config.LOCATIONS ("Askari") is the
    baseline and is dropped to avoid the dummy-variable trap.
    """
    categorical = pd.Categorical(location_series, categories=config.LOCATIONS)
    dummies = pd.get_dummies(categorical, prefix="Loc", drop_first=True)
    dummies.index = location_series.index if hasattr(location_series, "index") else dummies.index
    return dummies.astype(int)


def build_feature_matrix(df):
    """Build the model feature matrix: Plot_Area_SqYards + one-hot Location."""
    df = df.reset_index(drop=True)
    dummies = encode_locations(df["Location"])
    X = pd.concat([df[["Plot_Area_SqYards"]], dummies], axis=1)
    return X


def get_feature_columns():
    """The fixed, ordered list of feature-matrix columns the model expects."""
    dummy_cols = [f"Loc_{loc}" for loc in config.LOCATIONS[1:]]
    return ["Plot_Area_SqYards"] + dummy_cols


def prepare_training_data(df=None, test_size=0.2, random_state=None):
    """Full pipeline: load (if needed), clean, build features, split."""
    random_state = random_state if random_state is not None else config.RANDOM_SEED
    if df is None:
        df = load_dataset()
    df = clean_dataset(df)

    if len(df) < 10:
        raise ValueError(
            f"Only {len(df)} valid rows remain after cleaning — not enough to train a model."
        )

    X_full = build_feature_matrix(df)
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X_full, y, test_size=test_size, random_state=random_state
    )

    return {
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "feature_columns": get_feature_columns(),
        "cleaned_df": df,
    }
