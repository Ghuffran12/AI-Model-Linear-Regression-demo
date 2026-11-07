"""
Synthetic property dataset generator for the Corvit Huawei AI Demo.

This module is the direct descendant of the dataset-generation section
of the attached Colab script (its "1. GENERATE 100 HOUSE RECORDS"
block). The same idea — a documented base price, a documented
per-square-yard rate, and random noise simulating ordinary market
variation — is kept, but it has been:

  * extended from a single feature (house size) to also cover a
    sample "Location" field, as the project spec asks for,
  * extended from a 50-1,200 sq yard range to the full supported
    120-10,000 sq yard prediction range (with log-uniform sampling so
    small/medium plots are still well represented, not just huge ones),
  * made to generate internally-consistent Length and Breadth columns
    (Length x Breadth == Plot_Area_SqYards exactly, up to rounding),
  * parameterised through config.py instead of hardcoded constants.

IMPORTANT — Synthetic data disclosure (per project requirements):
No real property-market data was available for this demonstration.
Every record below is SYNTHETIC, produced from the documented formula
beneath, and must never be presented as a verified market valuation.

Documented pricing assumption
------------------------------
    deterministic_price = BASE_PRICE
                         + PRICE_PER_SQYD * Plot_Area_SqYards
                         + LOCATION_OFFSETS[Location]

    price = deterministic_price + noise,
            noise ~ Normal(0, min(NOISE_RELATIVE_STD * deterministic_price, NOISE_CAP_PKR))

The deterministic part is linear in Plot_Area_SqYards (continuous) and
in Location (categorical) by construction, which is exactly the
relationship the Linear Regression model in ml/train_model.py is
trained to recover. The noise term is proportional to each record's
own price (not a fixed PKR amount) so that ordinary "market noise"
stays realistic across the full 120-10,000 sq yd range instead of
vanishing for large, expensive plots -- see NOISE_RELATIVE_STD below.

NOISE_CAP_PKR exists for a specific, verified reason: price spans
roughly PKR 19M-1.5B across the supported area range, so uncapped
proportional noise reaches +-100M+ PKR for the largest plots -- far
bigger than any realistic LOCATION_OFFSETS value. Since OLS fits all
600 records together, those huge-area residuals would dominate the
location coefficients, which depend on only a handful of millions of
PKR of signal. (An earlier version of this generator had exactly that
bug: it fit a *positive* premium for a locality whose documented
LOCATION_OFFSETS entry is *negative*, purely from noise at the top of
the range swamping the signal -- confirmed by comparing the fitted
models/model_metadata.json coefficients against the dict below.)
Capping noise keeps it proportional -- and therefore realistic -- for
small and mid-size plots, while preventing it from drowning out a
small, fixed-size location effect at the expensive end.
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import config

# ---- Documented synthetic-pricing assumptions ---------------------------
BASE_PRICE = 800_000            # fixed base cost component (PKR)
PRICE_PER_SQYD = 150_000        # illustrative rate per square yard (PKR)
NOISE_RELATIVE_STD = 0.14       # simulated market noise: 14% of each record's
                                 # own deterministic price (NOT a fixed PKR
                                 # amount) -- see NOISE_CAP_PKR immediately
                                 # below for why this is also capped.
NOISE_CAP_PKR = 12_000_000      # absolute ceiling on the noise std, regardless
                                 # of how high NOISE_RELATIVE_STD * price goes.
                                 # Without this, noise for a ~10,000 sq yd plot
                                 # (price ~PKR 1.5B) would reach +-~200M PKR --
                                 # dwarfing every LOCATION_OFFSETS value below
                                 # and making locality statistically
                                 # unrecoverable from the generated data. The
                                 # cap keeps noise realistically proportional
                                 # for small/mid plots (where it rarely binds)
                                 # while bounding it for large ones, so BOTH
                                 # the area slope AND the per-locality offsets
                                 # stay honestly recoverable by OLS.
MIN_PRICE_FLOOR = 300_000       # a simulated price is never allowed below this

# Additive locality premium/discount relative to the "Askari" baseline.
# Keys must match config.LOCATIONS exactly. Magnitudes are chosen to be
# comfortably larger than NOISE_CAP_PKR / sqrt(samples per locality) --
# i.e. big enough to actually survive capped noise and be recoverable by
# the regression, not just big enough to "look right" by eye. Ordering
# (Clifton > DHA Phase 6 > Bahria Town > Askari > Gulshan-e-Iqbal) is an
# illustrative, documented assumption for this demo, not real market data.
LOCATION_OFFSETS = {
    "Askari": 0,
    "Gulshan-e-Iqbal": -3_000_000,
    "Bahria Town": 9_000_000,
    "DHA Phase 6": 16_000_000,
    "Clifton": 24_000_000,
}


def generate_dataset(n_samples=None, seed=None):
    """Generate a synthetic property dataset and return it as a DataFrame."""
    n_samples = n_samples or config.N_SAMPLES
    seed = seed if seed is not None else config.RANDOM_SEED
    rng = np.random.default_rng(seed)

    # Log-uniform sampling over the supported range gives realistic
    # coverage: proportionally more small/medium plots, fewer huge
    # ones, while still spanning 120 - 10,000 square yards end to end.
    areas = np.exp(
        rng.uniform(
            np.log(config.MIN_PREDICTION_SQYD),
            np.log(config.MAX_PREDICTION_SQYD),
            size=n_samples,
        )
    )

    # Random rectangular aspect ratio (breadth is 50%-100% of length),
    # then derive Length/Breadth so their product reproduces the area.
    aspect_ratios = rng.uniform(0.5, 1.0, size=n_samples)
    lengths = np.sqrt(areas / aspect_ratios)
    breadths = areas / lengths

    lengths = np.round(lengths, 2)
    breadths = np.round(breadths, 2)
    # Recompute area from the rounded dimensions so Plot_Area_SqYards,
    # Plot_Length_Yards and Plot_Breadth_Yards are always numerically
    # consistent in the stored dataset (Length x Breadth == Area).
    areas = np.round(lengths * breadths, 2)

    locations = rng.choice(config.LOCATIONS, size=n_samples)

    offsets = np.array([LOCATION_OFFSETS[loc] for loc in locations])
    deterministic_price = BASE_PRICE + PRICE_PER_SQYD * areas + offsets

    noise_std = np.minimum(NOISE_RELATIVE_STD * deterministic_price, NOISE_CAP_PKR)
    noise = rng.normal(0, noise_std, size=n_samples)
    prices = deterministic_price + noise
    prices = np.maximum(prices, MIN_PRICE_FLOOR)
    prices = np.round(prices).astype(int)

    property_ids = [f"PROP-{i + 1:04d}" for i in range(n_samples)]

    df = pd.DataFrame(
        {
            "Property_ID": property_ids,
            "Plot_Area_SqYards": areas,
            "Plot_Length_Yards": lengths,
            "Plot_Breadth_Yards": breadths,
            "Location": locations,
            "Property_Price": prices,
            "Currency": config.CURRENCY_CODE,
        }
    )

    return df


def save_dataset(path=None):
    """Generate the dataset and write it to CSV, creating folders as needed."""
    path = path or config.DATASET_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df = generate_dataset()
    df.to_csv(path, index=False)
    print(f"Generated {len(df)} synthetic property records -> {path}")
    return df


if __name__ == "__main__":
    save_dataset()
