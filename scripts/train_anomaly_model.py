from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from finance_ai.services.ml_workflow_service import ML_MODELS_DIR, train_model


def main() -> None:
    result = train_model(model_path=ML_MODELS_DIR / "anomaly_detector.pkl")
    print("Anomaly training workflow completed.")
    print("Shared pipeline artifact saved at:", result["model_path"])
    print(f"Accuracy: {result['accuracy']:.4f}")


if __name__ == "__main__":
    main()
