import os
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer

# ---------------------------------------------------
# 1️⃣ Load Dataset Safely
# ---------------------------------------------------

BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "loan_status_prediction.csv")

print("Loading dataset from:", DATA_PATH)

df = pd.read_csv(DATA_PATH)

print("Dataset Loaded Successfully")
print("Columns:", df.columns)
print("Shape:", df.shape)

# ---------------------------------------------------
# 2️⃣ Clean & Prepare Target
# ---------------------------------------------------

df["Loan_Status"] = df["Loan_Status"].str.upper()
df["Loan_Status"] = df["Loan_Status"].map({"Y": 1, "N": 0})

# Drop rows where target is missing
df = df.dropna(subset=["Loan_Status"])

# ---------------------------------------------------
# 3️⃣ Feature Selection
# ---------------------------------------------------

features = [
    "ApplicantIncome",
    "CoapplicantIncome",
    "LoanAmount",
    "Credit_History"
]

X = df[features]
y = df["Loan_Status"]

# ---------------------------------------------------
# 4️⃣ Preprocessing Pipeline
# ---------------------------------------------------

numeric_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

preprocessor = ColumnTransformer(
    transformers=[
        ("num", numeric_transformer, features)
    ]
)

# ---------------------------------------------------
# 5️⃣ Full ML Pipeline
# ---------------------------------------------------

model_pipeline = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("classifier", RandomForestClassifier(random_state=42))
])

# ---------------------------------------------------
# 6️⃣ Train / Test Split
# ---------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ---------------------------------------------------
# 7️⃣ Train Model
# ---------------------------------------------------

model_pipeline.fit(X_train, y_train)

accuracy = model_pipeline.score(X_test, y_test)
print(f"\nModel Accuracy: {accuracy:.2f}")

# ---------------------------------------------------
# 8️⃣ Save Model
# ---------------------------------------------------

MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")

joblib.dump(model_pipeline, MODEL_PATH)

print("Pipeline model trained and saved successfully!")
print("Model saved at:", MODEL_PATH)