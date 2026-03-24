from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, HTTPException
from pydantic import AliasChoices, BaseModel, Field

from finance_ai.services.ml_workflow_service import (
    SUPPORTED_MODEL_NAME,
    get_model_status,
    load_model,
    predict,
    save_loaded_model,
    train_model,
)


class TrainModelRequest(BaseModel):
    model_name: str = SUPPORTED_MODEL_NAME
    dataset_path: str | None = None
    model_path: str | None = None
    persist_model: bool = True
    load_after_train: bool = True


class LoadModelRequest(BaseModel):
    model_name: str = SUPPORTED_MODEL_NAME
    model_path: str | None = None
    force_reload: bool = False


class SaveModelRequest(BaseModel):
    model_name: str = SUPPORTED_MODEL_NAME
    model_path: str | None = None


class PredictionRequest(BaseModel):
    applicant_income: Annotated[
        float,
        Field(validation_alias=AliasChoices("ApplicantIncome", "applicant_income", "income")),
    ]
    coapplicant_income: Annotated[
        float,
        Field(validation_alias=AliasChoices("CoapplicantIncome", "coapplicant_income")),
    ] = 0.0
    loan_amount: Annotated[
        float,
        Field(validation_alias=AliasChoices("LoanAmount", "loan_amount")),
    ]
    credit_history: Annotated[
        float,
        Field(validation_alias=AliasChoices("Credit_History", "credit_history")),
    ]
    model_name: str = SUPPORTED_MODEL_NAME
    model_path: str | None = None
    persist_log: bool = True


app = FastAPI(
    title="Finance AI ML API",
    version="1.0.0",
    description=(
        "FastAPI wrapper for the existing local ML workflow. "
        "Use it to train, save, load, and run predictions through REST endpoints."
    ),
)


@app.get("/")
def root() -> dict[str, object]:
    return {
        "message": "Finance AI ML API is running",
        "docs_url": "/docs",
        "health_url": "/health",
        "supported_model": SUPPORTED_MODEL_NAME,
    }


@app.get("/health")
def health_check() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "finance-ai-ml-api",
        "model_status": get_model_status(),
    }


@app.get("/api/v1/models/status")
def model_status() -> dict[str, object]:
    return {
        "status": "success",
        "data": get_model_status(),
    }


@app.post("/api/v1/models/train")
def train_model_endpoint(payload: TrainModelRequest) -> dict[str, object]:
    try:
        result = train_model(
            model_name=payload.model_name,
            dataset_path=payload.dataset_path,
            model_path=payload.model_path,
            persist_model=payload.persist_model,
            load_after_train=payload.load_after_train,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "status": "success",
        "message": "Model trained successfully",
        "data": result,
    }


@app.post("/api/v1/models/load")
def load_model_endpoint(payload: LoadModelRequest) -> dict[str, object]:
    try:
        result = load_model(
            model_name=payload.model_name,
            model_path=payload.model_path,
            force_reload=payload.force_reload,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "status": "success",
        "message": "Model loaded successfully",
        "data": result,
    }


@app.post("/api/v1/models/save")
def save_model_endpoint(payload: SaveModelRequest) -> dict[str, object]:
    try:
        result = save_loaded_model(
            model_name=payload.model_name,
            model_path=payload.model_path,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "status": "success",
        "message": "Loaded model saved successfully",
        "data": result,
    }


@app.post("/api/v1/predict")
def predict_endpoint(payload: PredictionRequest) -> dict[str, object]:
    try:
        result = predict(
            applicant_income=payload.applicant_income,
            coapplicant_income=payload.coapplicant_income,
            loan_amount=payload.loan_amount,
            credit_history=payload.credit_history,
            model_name=payload.model_name,
            model_path=payload.model_path,
            persist_log=payload.persist_log,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "status": "success",
        "message": "Prediction generated successfully",
        "data": result,
    }
