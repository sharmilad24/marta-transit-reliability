import sqlite3
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import joblib

# 1. Load the clean data
conn = sqlite3.connect("marta_data.db")
df = pd.read_sql_query("SELECT * FROM clean_arrivals", conn)
conn.close()
print(f"Loaded {len(df):,} rows")

# 2. Drop clearly-bad outliers (readings more than ~10-15 min off schedule)
df = df[(df["delay_seconds"] >= -600) & (df["delay_seconds"] <= 900)]
print(f"{len(df):,} rows after removing extreme outliers")

# 3. Choose features (the inputs) and target (what we predict)
features = ["line", "station", "direction", "hour_of_day", "day_of_week"]
X = df[features]
y = df["delay_seconds"]

# 4. Turn text categories into numbers the model can use (one-hot encoding)
X = pd.get_dummies(X, columns=["line", "station", "direction"])

# 5. Split: train on 80% of the data, test on the unseen 20%
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 6. Train the model
model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

# 7. Evaluate vs a simple baseline ("always guess the average delay")
baseline = y_train.mean()
baseline_mae = mean_absolute_error(y_test, [baseline] * len(y_test))
model_mae = mean_absolute_error(y_test, model.predict(X_test))

print(f"\nBaseline (always guess average): off by {baseline_mae:.1f} sec on average")
print(f"Your model:                      off by {model_mae:.1f} sec on average")
print(f"Improvement over baseline: {(baseline_mae - model_mae) / baseline_mae * 100:.1f}%")

# 8. Which factors matter most?
importances = pd.Series(model.feature_importances_, index=X.columns)
print("\nTop 10 most important factors:")
print(importances.sort_values(ascending=False).head(10))

# 9. Save the trained model for later use
joblib.dump(model, "delay_model.pkl")
print("\nModel saved to delay_model.pkl")