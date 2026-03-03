from sqlalchemy import Column, Integer, String, Text
from finance_ai.db import Base


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True)
    input_data = Column(Text, nullable=False)
    prediction = Column(String(100), nullable=False)