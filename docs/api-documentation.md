# API Documentation

## FastAPI ML API

Base URL when running `.\scripts\start-fastapi.ps1`:

`http://localhost:8000`

Interactive docs:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

### Health Check

`GET /health`

Example response:

```json
{
  "status": "ok",
  "service": "finance-ai-ml-api"
}
```

### Train Model

`POST /api/v1/models/train`

Example body:

```json
{
  "model_name": "loan_approval",
  "persist_model": true,
  "load_after_train": true
}
```

### Load Model

`POST /api/v1/models/load`

Example body:

```json
{
  "model_name": "loan_approval",
  "force_reload": false
}
```

### Save Model

`POST /api/v1/models/save`

Example body:

```json
{
  "model_name": "loan_approval"
}
```

### Predict

`POST /api/v1/predict`

The API accepts either the original feature names or snake_case names.

Example body:

```json
{
  "ApplicantIncome": 5000,
  "CoapplicantIncome": 1500,
  "LoanAmount": 120,
  "Credit_History": 1
}
```

Postman-friendly alternative:

```json
{
  "applicant_income": 5000,
  "coapplicant_income": 1500,
  "loan_amount": 120,
  "credit_history": 1
}
```

### Model Status

`GET /api/v1/models/status`
