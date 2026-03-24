from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sqlalchemy import create_engine
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from finance_ai.models import Base, DBSession, PredictionLog


FEATURES = [
    "ApplicantIncome",
    "CoapplicantIncome",
    "LoanAmount",
    "Credit_History",
]
TARGET_COLUMN = "Loan_Status"
SUPPORTED_MODEL_NAME = "loan_approval"

BACKEND_DIR = Path(__file__).resolve().parents[2]
ML_MODELS_DIR = BACKEND_DIR / "finance_ai" / "ml_models"
DEFAULT_DATASET_PATH = ML_MODELS_DIR / "loan_status_prediction.csv"
DEFAULT_MODEL_PATH = ML_MODELS_DIR / "model.pkl"
DEFAULT_DB_PATH = BACKEND_DIR / "finance_ai.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"

_LOADED_MODEL: Any | None = None
_LOADED_MODEL_PATH: Path | None = None
_LOADED_AT: datetime | None = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_path(path: str | Path | None, default: Path) -> Path:
    if path is None:
        return default

    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = BACKEND_DIR / candidate
    return candidate.resolve()


def _validate_supported_model(model_name: str) -> None:
    if model_name != SUPPORTED_MODEL_NAME:
        raise ValueError(
            f"Unsupported model '{model_name}'. Supported models: {SUPPORTED_MODEL_NAME}"
        )


def _build_pipeline() -> Pipeline:
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[("num", numeric_transformer, FEATURES)]
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", RandomForestClassifier(random_state=42)),
        ]
    )


def _prepare_training_dataframe(dataset_path: Path) -> pd.DataFrame:
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")

    df = pd.read_csv(dataset_path)
    required_columns = set(FEATURES + [TARGET_COLUMN])
    missing = sorted(required_columns.difference(df.columns))
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(missing)}")

    df[TARGET_COLUMN] = df[TARGET_COLUMN].astype(str).str.upper().map({"Y": 1, "N": 0})
    df = df.dropna(subset=[TARGET_COLUMN])
    return df


def _set_loaded_model(model: Any, model_path: Path | None) -> None:
    global _LOADED_AT, _LOADED_MODEL, _LOADED_MODEL_PATH

    _LOADED_MODEL = model
    _LOADED_MODEL_PATH = model_path
    _LOADED_AT = _utc_now()


def train_model(
    model_name: str = SUPPORTED_MODEL_NAME,
    dataset_path: str | Path | None = None,
    model_path: str | Path | None = None,
    persist_model: bool = True,
    load_after_train: bool = True,
) -> dict[str, Any]:
    _validate_supported_model(model_name)

    resolved_dataset_path = _normalize_path(dataset_path, DEFAULT_DATASET_PATH)
    resolved_model_path = _normalize_path(model_path, DEFAULT_MODEL_PATH)

    df = _prepare_training_dataframe(resolved_dataset_path)
    X = df[FEATURES]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model_pipeline = _build_pipeline()
    model_pipeline.fit(X_train, y_train)
    accuracy = float(model_pipeline.score(X_test, y_test))

    if persist_model:
        resolved_model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model_pipeline, resolved_model_path)

    if load_after_train:
        _set_loaded_model(model_pipeline, resolved_model_path if persist_model else None)

    return {
        "model_name": model_name,
        "dataset_path": str(resolved_dataset_path),
        "model_path": str(resolved_model_path),
        "persisted": persist_model,
        "loaded_after_train": load_after_train,
        "rows_used": int(len(df)),
        "features": FEATURES,
        "accuracy": round(accuracy, 4),
        "trained_at": _utc_now().isoformat(),
    }


def load_model(
    model_name: str = SUPPORTED_MODEL_NAME,
    model_path: str | Path | None = None,
    force_reload: bool = False,
) -> dict[str, Any]:
    _validate_supported_model(model_name)

    resolved_model_path = _normalize_path(model_path, DEFAULT_MODEL_PATH)
    if not resolved_model_path.exists():
        raise FileNotFoundError(f"Model file not found at {resolved_model_path}")

    if (
        not force_reload
        and _LOADED_MODEL is not None
        and _LOADED_MODEL_PATH == resolved_model_path
    ):
        return {
            "model_name": model_name,
            "model_path": str(resolved_model_path),
            "loaded": True,
            "cached": True,
            "loaded_at": _LOADED_AT.isoformat() if _LOADED_AT else None,
        }

    model = joblib.load(resolved_model_path)
    _set_loaded_model(model, resolved_model_path)

    return {
        "model_name": model_name,
        "model_path": str(resolved_model_path),
        "loaded": True,
        "cached": False,
        "loaded_at": _LOADED_AT.isoformat() if _LOADED_AT else None,
    }


def save_loaded_model(
    model_name: str = SUPPORTED_MODEL_NAME,
    model_path: str | Path | None = None,
) -> dict[str, Any]:
    _validate_supported_model(model_name)

    if _LOADED_MODEL is None:
        raise ValueError("No model is currently loaded in memory")

    resolved_model_path = _normalize_path(model_path, DEFAULT_MODEL_PATH)
    resolved_model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(_LOADED_MODEL, resolved_model_path)
    _set_loaded_model(_LOADED_MODEL, resolved_model_path)

    return {
        "model_name": model_name,
        "model_path": str(resolved_model_path),
        "saved": True,
        "saved_at": _utc_now().isoformat(),
    }


def get_model_status() -> dict[str, Any]:
    default_exists = DEFAULT_MODEL_PATH.exists()
    return {
        "supported_models": [SUPPORTED_MODEL_NAME],
        "loaded": _LOADED_MODEL is not None,
        "loaded_model_path": str(_LOADED_MODEL_PATH) if _LOADED_MODEL_PATH else None,
        "loaded_at": _LOADED_AT.isoformat() if _LOADED_AT else None,
        "default_model_path": str(DEFAULT_MODEL_PATH),
        "default_model_exists": default_exists,
        "default_model_size_bytes": DEFAULT_MODEL_PATH.stat().st_size if default_exists else 0,
    }


def _ensure_db_ready(database_url: str = DEFAULT_DATABASE_URL) -> None:
    bind = getattr(DBSession, "kw", {}).get("bind")
    if bind is not None:
        return

    engine = create_engine(database_url)
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)


def _log_prediction(
    applicant_income: float,
    coapplicant_income: float,
    loan_amount: float,
    credit_history: float,
    prediction: str,
) -> None:
    _ensure_db_ready()
    session = DBSession()
    try:
        session.add(
            PredictionLog(
                applicant_income=applicant_income,
                coapplicant_income=coapplicant_income,
                loan_amount=loan_amount,
                credit_history=credit_history,
                prediction=prediction,
                created_at=datetime.utcnow(),
            )
        )
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def predict(
    applicant_income: float,
    coapplicant_income: float,
    loan_amount: float,
    credit_history: float,
    model_name: str = SUPPORTED_MODEL_NAME,
    model_path: str | Path | None = None,
    persist_log: bool = True,
) -> dict[str, Any]:
    _validate_supported_model(model_name)

    resolved_model_path = _normalize_path(model_path, DEFAULT_MODEL_PATH)
    if _LOADED_MODEL is None or _LOADED_MODEL_PATH != resolved_model_path:
        load_model(model_name=model_name, model_path=resolved_model_path)

    row = {
        "ApplicantIncome": applicant_income,
        "CoapplicantIncome": coapplicant_income,
        "LoanAmount": loan_amount,
        "Credit_History": credit_history,
    }
    X = pd.DataFrame([row], columns=FEATURES)

    probability_approved = None
    if hasattr(_LOADED_MODEL, "predict_proba"):
        probability_approved = float(_LOADED_MODEL.predict_proba(X)[0][1])

    y_pred = int(_LOADED_MODEL.predict(X)[0])
    prediction_label = "Approved" if y_pred == 1 else "Rejected"

    if persist_log:
        _log_prediction(
            applicant_income=applicant_income,
            coapplicant_income=coapplicant_income,
            loan_amount=loan_amount,
            credit_history=credit_history,
            prediction=prediction_label,
        )

    return {
        "model_name": model_name,
        "model_path": str(resolved_model_path),
        "prediction": prediction_label,
        "prediction_code": y_pred,
        "probability_approved": (
            round(probability_approved, 6)
            if probability_approved is not None
            else None
        ),
        "input": row,
        "logged_to_db": persist_log,
        "predicted_at": _utc_now().isoformat(),
    }
