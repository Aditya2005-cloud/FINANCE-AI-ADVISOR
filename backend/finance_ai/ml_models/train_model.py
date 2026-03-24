from finance_ai.services.ml_workflow_service import train_model


def main() -> None:
    result = train_model()
    print("Dataset Loaded Successfully")
    print("Rows used:", result["rows_used"])
    print("Features:", ", ".join(result["features"]))
    print(f"Model Accuracy: {result['accuracy']:.4f}")
    print("Pipeline model trained and saved successfully!")
    print("Model saved at:", result["model_path"])


if __name__ == "__main__":
    main()
