from pyramid.view import view_config
from sqlalchemy import func

from finance_ai.models import DBSession, PredictionLog


@view_config(route_name="predictions", renderer="json", request_method="GET")
@view_config(route_name="api_predictions", renderer="json", request_method="GET")
def get_predictions(request):
    session = DBSession()

    try:
        total = session.query(func.count(PredictionLog.id)).scalar() or 0

        approved = (
            session.query(func.count(PredictionLog.id))
            .filter(PredictionLog.prediction == "Approved")
            .scalar()
            or 0
        )

        rejected = (
            session.query(func.count(PredictionLog.id))
            .filter(PredictionLog.prediction == "Rejected")
            .scalar()
            or 0
        )

        approval_rate = (approved / total * 100) if total > 0 else 0

        recent_logs = (
            session.query(PredictionLog)
            .order_by(PredictionLog.id.desc())
            .limit(20)
            .all()
        )

        logs_data = [
            {
                "id": log.id,
                "applicant_income": log.applicant_income,
                "coapplicant_income": log.coapplicant_income,
                "loan_amount": log.loan_amount,
                "credit_history": log.credit_history,
                "prediction": log.prediction,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in recent_logs
        ]

        return {
            "status": "success",
            "statistics": {
                "total_predictions": total,
                "approved": approved,
                "rejected": rejected,
                "approval_rate_percent": round(approval_rate, 2),
            },
            "recent_predictions": logs_data,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }

    finally:
        session.close()
