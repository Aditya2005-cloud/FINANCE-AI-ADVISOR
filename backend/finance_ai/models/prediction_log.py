from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from .meta import Base


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True)
    applicant_income = Column(Float, nullable=False)
    coapplicant_income = Column(Float, nullable=False)
    loan_amount = Column(Float, nullable=False)
    credit_history = Column(Float, nullable=False)
    prediction = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
