import unittest

from finance_ai.models.prediction_log import PredictionLog


class PredictionLogModelTests(unittest.TestCase):
    def test_model_has_expected_columns(self):
        columns = PredictionLog.__table__.columns

        for name in [
            "id",
            "applicant_income",
            "coapplicant_income",
            "loan_amount",
            "credit_history",
            "prediction",
            "created_at",
        ]:
            self.assertIn(name, columns)

    def test_created_at_is_non_nullable(self):
        self.assertFalse(PredictionLog.__table__.columns["created_at"].nullable)


if __name__ == "__main__":
    unittest.main()
