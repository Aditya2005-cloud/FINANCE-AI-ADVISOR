import os
from datetime import datetime

import joblib
import pandas as pd
from pyramid.view import view_config

from finance_ai.models import DBSession, PredictionLog


_BASE_DIR = os.path.dirname(os.path.dirname(__file__))
_MODEL_PATH = os.path.join(_BASE_DIR, "ml_models", "model.pkl")
_FEATURES = ["ApplicantIncome", "CoapplicantIncome", "LoanAmount", "Credit_History"]
_MODEL = joblib.load(_MODEL_PATH)


@view_config(route_name="predict", renderer="json", request_method="POST")
@view_config(route_name="api_predict", renderer="json", request_method="POST")
def predict_view(request):
    db = DBSession()

    try:
        data = request.json_body or {}

        applicant_income = float(data.get("ApplicantIncome") or data.get("income", 0) or 0)
        coapplicant_income = float(data.get("CoapplicantIncome") or data.get("coapplicant_income", 0) or 0)
        loan_amount = float(data.get("LoanAmount") or data.get("loan_amount", 0) or 0)
        credit_history = float(data.get("Credit_History") or data.get("credit_history", 0) or 0)

        row = {
            "ApplicantIncome": applicant_income,
            "CoapplicantIncome": coapplicant_income,
            "LoanAmount": loan_amount,
            "Credit_History": credit_history,
        }

        X = pd.DataFrame([row], columns=_FEATURES)

        if hasattr(_MODEL, "predict_proba"):
            proba = float(_MODEL.predict_proba(X)[0][1])
        else:
            proba = None

        y_pred = _MODEL.predict(X)[0]
        result = "Approved" if int(y_pred) == 1 else "Rejected"

        new_log = PredictionLog(
            applicant_income=applicant_income,
            coapplicant_income=coapplicant_income,
            loan_amount=loan_amount,
            credit_history=credit_history,
            prediction=result,
            created_at=datetime.utcnow(),
        )

        db.add(new_log)
        db.commit()

        return {
            "status": "success",
            "prediction": result,
            "probability_approved": proba,
        }

    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": str(e),
        }

    finally:
        db.close()
