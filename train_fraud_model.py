# train_model.py
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import pickle

# --- Step 1: Create Sample Data ---
np.random.seed(42)
amounts = np.random.randint(100, 100000, 500)
labels = [1 if amt > 50000 else 0 for amt in amounts]
df = pd.DataFrame({"amount": amounts, "fraud": labels})

# --- Step 2: Train-Test Split ---
X = df[["amount"]].astype(float)  # ensure numeric
y = df["fraud"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# --- Step 3: Train Model ---
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

print("✅ Model trained with accuracy:", model.score(X_test, y_test))

# --- Step 4: Save Model ---
with open("fraud_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("📁 fraud_model.pkl saved successfully!")