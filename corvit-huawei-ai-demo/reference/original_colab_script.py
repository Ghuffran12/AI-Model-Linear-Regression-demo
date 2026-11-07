# ============================================================
# REFERENCE COPY — kept verbatim, unmodified, for direct comparison.
#
# This is exactly the Python/Google-Colab script the user attached to
# the original project brief for "Corvit Huawei AI Demo" (single
# feature: House_Size_SqYards -> House_Price_PKR, sklearn
# LinearRegression, train_test_split(test_size=0.20, random_state=42),
# MAE/R^2 evaluation, ipywidgets for interactive input). It is NOT
# imported or executed anywhere in the application — ipywidgets/
# IPython.display aren't even in requirements.txt, since they only
# make sense inside a Colab/Jupyter notebook.
#
# It is preserved here, unedited, so its logic can be compared line by
# line against where it actually ended up. See README.md section 11
# ("Provenance") for the file-by-file mapping, and the module
# docstrings at the top of ml/generate_dataset.py, ml/data_preprocessing.py,
# ml/train_model.py and ml/predict.py for exactly what was kept,
# changed, and why.
# ============================================================

# ============================================================
# HOUSE PRICE PREDICTION USING LINEAR REGRESSION
# Platform: Google Colab
# Dataset: 100 house records
# Currency: PKR (illustrative simulated prices)
# ============================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ipywidgets as widgets

from IPython.display import display, clear_output
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# ------------------------------------------------------------
# 1. GENERATE 100 HOUSE RECORDS
# ------------------------------------------------------------

np.random.seed(42)

# Generate 100 house sizes, ranging from 50 to 1200 square yards
house_sizes = np.random.randint(50, 1201, size=100)

# Include the required house sizes
house_sizes[:4] = [80, 120, 400, 1000]

# Illustrative pricing formula:
# Base price = PKR 1,500,000
# Additional price = PKR 120,000 per square yard
# Random noise simulates differences between houses
base_price = 1_500_000
price_per_sq_yard = 120_000

noise = np.random.normal(0, 1_000_000, size=100)

house_prices = (
    base_price
    + price_per_sq_yard * house_sizes
    + noise
)

# Keep simulated prices positive
house_prices = np.maximum(house_prices, 500_000)

df = pd.DataFrame({
    "House_Size_SqYards": house_sizes,
    "House_Price_PKR": np.round(house_prices, 0).astype(int)
})

print("========== HOUSE PRICE DATASET ==========")
print("Total records:", len(df))
display(df)

# ------------------------------------------------------------
# 2. PREPARE DATA FOR MACHINE LEARNING
# ------------------------------------------------------------

X = df[["House_Size_SqYards"]]
y = df["House_Price_PKR"]

# Split into training and testing datasets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42
)

# ------------------------------------------------------------
# 3. TRAIN LINEAR REGRESSION MODEL
# ------------------------------------------------------------

model = LinearRegression()
model.fit(X_train, y_train)

# Model evaluation on unseen test records
test_predictions = model.predict(X_test)

mae = mean_absolute_error(y_test, test_predictions)
r2 = r2_score(y_test, test_predictions)

print("\n========== MODEL TRAINING ==========")
print("Training records:", len(X_train))
print("Testing records:", len(X_test))

print("\nLearned Linear Regression Formula:")
print(
    f"House Price = {model.intercept_:,.2f} "
    f"+ ({model.coef_[0]:,.2f} x House Size)"
)

print(f"\nTest Mean Absolute Error: PKR {mae:,.0f}")
print(f"Test R-squared Score: {r2:.3f}")

# ------------------------------------------------------------
# 4. PREDICT HOUSE VALUE FOR ANY SIZE
# ------------------------------------------------------------

def predict_house_price(size):
    if size <= 0:
        print("Please enter a house size greater than zero.")
        return

    input_data = pd.DataFrame({
        "House_Size_SqYards": [size]
    })

    predicted_price = model.predict(input_data)[0]

    print("\n========== HOUSE PRICE PREDICTION ==========")
    print(f"House Size: {size:,} square yards")
    print(f"Estimated House Value: PKR {predicted_price:,.0f}")
    print(f"Estimated Value in Crore: {predicted_price / 10_000_000:.2f}")
    print("\nNote: This is an illustrative model estimate,")
    print("not an actual property market valuation.")

# ------------------------------------------------------------
# 5. INTERACTIVE HOUSE SIZE INPUT
# ------------------------------------------------------------

house_size_input = widgets.IntText(
    value=80,
    description="House Size:",
    style={"description_width": "initial"}
)

predict_button = widgets.Button(
    description="Calculate House Value",
    button_style="success",
    icon="calculator"
)

output = widgets.Output()

def on_predict_clicked(button):
    with output:
        clear_output(wait=True)
        predict_house_price(house_size_input.value)

predict_button.on_click(on_predict_clicked)

print("\n========== ENTER HOUSE SIZE ==========")
print("Enter any house size in square yards.")

display(widgets.VBox([
    house_size_input,
    predict_button,
    output
]))

# ------------------------------------------------------------
# 6. TEST THE FOUR REQUIRED HOUSE SIZES
# ------------------------------------------------------------

print("\n========== SAMPLE SIZE PREDICTIONS ==========")

sample_sizes = [80, 120, 400, 1000]

sample_data = pd.DataFrame({
    "House_Size_SqYards": sample_sizes
})

sample_predictions = model.predict(sample_data)

sample_results = pd.DataFrame({
    "House_Size_SqYards": sample_sizes,
    "Estimated_Price_PKR": np.round(
        sample_predictions
    ).astype(int)
})

display(sample_results)

# ------------------------------------------------------------
# 7. VISUALIZE THE REGRESSION LINE
# ------------------------------------------------------------

plt.figure(figsize=(10, 6))

plt.scatter(
    X_train["House_Size_SqYards"],
    y_train,
    label="Training houses"
)

plt.scatter(
    X_test["House_Size_SqYards"],
    y_test,
    label="Testing houses"
)

plot_sizes = np.linspace(
    df["House_Size_SqYards"].min(),
    df["House_Size_SqYards"].max(),
    200
)

plot_data = pd.DataFrame({
    "House_Size_SqYards": plot_sizes
})

plt.plot(
    plot_sizes,
    model.predict(plot_data),
    label="Linear Regression Line"
)

plt.xlabel("House Size (Square Yards)")
plt.ylabel("House Price (PKR)")
plt.title("House Price Prediction Using Linear Regression")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()

# ============================================================
# END OF HOUSE PRICE PREDICTION PROJECT
# ============================================================
