# `data/property_data.csv`

This dataset is **synthetic**. It was generated for the Corvit Huawei AI
Demo by `ml/generate_dataset.py` — no real property-market data was
collected or used anywhere in this project. Treat every price in this
file as an illustrative demonstration value, never as a real valuation.

## Columns

| Column                | Type    | Description                                                        |
|------------------------|---------|----------------------------------------------------------------------|
| `Property_ID`          | string  | Synthetic identifier, e.g. `PROP-0001`.                              |
| `Plot_Area_SqYards`    | float   | Plot area in square yards — the model's primary numeric feature.    |
| `Plot_Length_Yards`    | float   | Plot length in yards. `Length x Breadth == Plot_Area_SqYards`.       |
| `Plot_Breadth_Yards`   | float   | Plot breadth/width in yards.                                        |
| `Location`             | string  | One of the five sample localities in `config.LOCATIONS` — the model's second feature (one-hot encoded). |
| `Property_Price`       | integer | Target variable: the synthetic price, in whole currency units.       |
| `Currency`             | string  | Always `PKR` by default (see `config.CURRENCY_CODE`).                |

## How the prices were generated

See the full documented formula and reasoning at the top of
`ml/generate_dataset.py`. In short:

```
deterministic_price = BASE_PRICE + PRICE_PER_SQYD * Plot_Area_SqYards + LOCATION_OFFSETS[Location]
price = deterministic_price + noise,   noise ~ Normal(0, min(0.14 * deterministic_price, NOISE_CAP_PKR))
```

- `BASE_PRICE` and `PRICE_PER_SQYD` are illustrative constants, in the
  same spirit as the `base_price` / `price_per_sq_yard` assumptions in
  the originally-attached Colab script, extended to the project's
  120–10,000 sq yard range.
- `LOCATION_OFFSETS` is a fixed, documented premium/discount per
  locality relative to the `Askari` baseline, sized to stay
  recoverable against the (capped) noise below -- see the ordering and
  magnitudes in `ml/generate_dataset.py`.
- Noise is **proportional** to each record's own price (not a fixed
  PKR amount) up to `NOISE_CAP_PKR` (PKR 12,000,000), so variance
  stays realistic across both small and large plots instead of
  vanishing for expensive ones -- but is also capped, because
  uncapped proportional noise on a ~PKR 1.5B plot (the top of the
  supported range) would reach +-~200M PKR and statistically swamp
  every `LOCATION_OFFSETS` value, making locality unrecoverable by the
  regression no matter how real its effect was in the generating
  formula. Both the area slope and the per-locality offsets are
  checked, after every training run, to come out with plausible
  signs and magnitudes -- not just a high R².
- Plot area is sampled log-uniformly across 120–10,000 sq yards, so
  small/medium plots are well represented rather than crowded out by
  large ones.
- Length and breadth are derived from a random aspect ratio so that
  `Length x Breadth` always reproduces `Plot_Area_SqYards` exactly (up
  to rounding) — they are stored for reference/display and for the
  dimensions calculator, but are **not** fed into the regression as
  separate features alongside area (see `ml/data_preprocessing.py`'s
  module docstring for why: area, length and breadth are mathematically
  dependent, and including all three would create unnecessary
  multicollinearity).

## Regenerating or replacing this dataset

To regenerate a fresh synthetic dataset with the same assumptions:

```bash
python ml/generate_dataset.py
python ml/train_model.py
```

To use **real** property data instead:

1. Replace this CSV with your own file, keeping the same column names
   (or update `REQUIRED_COLUMNS` in `ml/data_preprocessing.py` to
   match).
2. If you introduce new localities, add them to `config.LOCATIONS`
   first — the model only has a trained coefficient for localities it
   has seen, and `ml/data_preprocessing.clean_dataset()` drops any row
   whose `Location` isn't in that list.
3. Re-run `python ml/train_model.py` to retrain on the new data.
4. Update the disclaimers in `templates/about.html`, `templates/base.html`
   and the `/api/predict` response in `app.py` — they currently say the
   data is synthetic, which would no longer be true.
