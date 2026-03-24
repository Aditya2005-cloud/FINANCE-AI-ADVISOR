import unittest

from fastapi.testclient import TestClient

from finance_ai.fastapi_app import app


class FastAPIMLApiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint_returns_ok(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("model_status", payload)

    def test_openapi_includes_predict_endpoint(self):
        response = self.client.get("/openapi.json")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("/api/v1/predict", payload["paths"])


if __name__ == "__main__":
    unittest.main()
