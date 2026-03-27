# FINANCE-AI-ADVISOR

AI-powered finance advisor project with:

- a Pyramid backend for the existing application flow
- a FastAPI ML service for training and inference APIs
- a React frontend for the user interface

## Preview

<img width="1281" height="733" alt="{52FC3C71-9483-4BAE-9340-D22CA12F0B29}" src="https://github.com/user-attachments/assets/26490c5c-3a05-4b5a-aa97-c5dda9566940" />
<img width="1145" height="644" alt="{A6361EA5-4B7F-48B7-B2B8-FBA997C9120B}" src="https://github.com/user-attachments/assets/3412c6ba-191f-4a64-9c1e-974411427c30" />
<img width="1158" height="479" alt="{2BD89FB3-AD02-47C7-A909-D8471A0FBDEB}" src="https://github.com/user-attachments/assets/3d88ab42-7adc-49b9-9987-cea4f27ba825" />
<img width="1113" height="432" alt="{F3EFBBAE-884F-4EB8-AF3C-4BB1DD95C9A9}" src="https://github.com/user-attachments/assets/87ea6bd9-e524-4509-b7db-36cc67d4e1bf" />
<img width="716" height="500" alt="{00EA31E0-FA43-4477-BF54-50837FEC54F0}" src="https://github.com/user-attachments/assets/8354b7ad-ce20-4a21-933f-cadbd2d8d07e" />

## Features

- Loan approval prediction using a trained scikit-learn pipeline
- Prediction history persisted in SQLite
- FastAPI endpoints for training, loading, saving, and prediction
- Automatic Swagger and ReDoc documentation
- Postman-friendly JSON request/response workflow
- AI financial file analysis endpoints
- Follow-up advisor chat endpoints
- Local scripts for backend, frontend, and test execution

## Project Structure

```text
FINANCE-AI-ADVISOR/
|-- backend/
|   |-- finance_ai/
|   |   |-- fastapi_app.py
|   |   |-- services/
|   |   |   `-- ml_workflow_service.py
|   |   `-- ml_models/
|   |       |-- train_model.py
|   |       |-- model.pkl
|   |       `-- loan_status_prediction.csv
|   `-- tests/
|-- frontend/
|-- scripts/
|   |-- start-backend.ps1
|   |-- start-fastapi.ps1
|   |-- start-frontend.ps1
|   |-- train_expense_model.py
|   `-- train_anomaly_model.py
`-- docs/
```

## Installation

### 1. Clone repository

```powershell
git clone <YOUR_GITHUB_REPO_URL>
cd FINANCE-AI-ADVISOR
```

### 2. Backend setup

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
cd ..
```

### 3. Frontend setup

```powershell
cd frontend
npm install
cd ..
```

## How To Run

### Pyramid backend

```powershell
.\scripts\start-backend.ps1
```

Default URL: `http://localhost:6543`

### FastAPI ML API

```powershell
.\scripts\start-fastapi.ps1
```

Default URL: `http://localhost:8000`

Docs:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

### React frontend

```powershell
.\scripts\start-frontend.ps1
```

Default URL: `http://localhost:5173`

### Run both app layers

```powershell
.\scripts\start-all.ps1
```

## Docker Hub Quickstart

Published image:

- `n8nproject2026/finance-ai-advisor:latest`

This image supports two backend modes:

- `APP_MODE=pyramid` runs the Pyramid backend on port `6543`
- `APP_MODE=fastapi` runs the FastAPI backend on port `8000`

### Step 1. Pull the image

```powershell
docker pull n8nproject2026/finance-ai-advisor:latest
```

### Step 2. Start the FastAPI backend

This backend handles prediction and AI upload/chat fallback:

```powershell
docker run --name finance-fastapi --rm -p 8000:8000 -e APP_MODE=fastapi n8nproject2026/finance-ai-advisor:latest
```

Open in browser after startup:

- `http://localhost:8000/health`
- `http://localhost:8000/docs`

### Step 3. Start the Pyramid backend

This backend handles the original app routes and prediction history dashboard:

```powershell
docker run --name finance-pyramid --rm -p 6543:6543 -e APP_MODE=pyramid n8nproject2026/finance-ai-advisor:latest
```

Open in browser after startup:

- `http://localhost:6543/`

### Step 4. Start the frontend locally

Open a new terminal:

```powershell
cd frontend
$env:VITE_PYRAMID_API_ORIGIN="http://localhost:6543"
$env:VITE_FASTAPI_API_ORIGIN="http://localhost:8000"
npm install
npm run dev
```

Then open:

- `http://localhost:5173`

### Step 5. Test the app

1. Run a loan prediction.
2. Upload a `.csv`, `.txt`, `.json`, or `.xlsx` file in the AI advisor section.
3. Ask a follow-up question after analysis completes.

### One-container examples

If you only want one backend:

FastAPI only:

```powershell
docker run --name finance-fastapi --rm -p 8000:8000 -e APP_MODE=fastapi n8nproject2026/finance-ai-advisor:latest
```

Pyramid only:

```powershell
docker run --name finance-pyramid --rm -p 6543:6543 -e APP_MODE=pyramid n8nproject2026/finance-ai-advisor:latest
```

### Stop the containers

```powershell
docker stop finance-fastapi
docker stop finance-pyramid
```

### Troubleshooting

- If the frontend shows `Server returned non-JSON response (500)`, first confirm both backends are running.
- If Docker Desktop is used, create two containers, not one. One container should use `APP_MODE=fastapi`, and the other should use `APP_MODE=pyramid`.
- If you updated the image recently, pull again before starting:

```powershell
docker pull n8nproject2026/finance-ai-advisor:latest
```

### For users who want to build locally

```powershell
docker build -f backend/Dockerfile -t finance-ai-advisor:latest .
```

### For repository owners who want to publish updates

```powershell
docker login
docker build -f backend/Dockerfile -t n8nproject2026/finance-ai-advisor:latest .
docker push n8nproject2026/finance-ai-advisor:latest
```

## ML Workflow

The existing workflow is preserved:

1. Train the model locally
2. Save the model as a local artifact
3. Load the saved model
4. Send inputs for prediction
5. Return results as API responses instead of terminal-only output

Active model artifact:

- `backend/finance_ai/ml_models/model.pkl`

Training dataset:

- `backend/finance_ai/ml_models/loan_status_prediction.csv`

### Local training

```powershell
cd backend
.\venv\Scripts\python.exe .\finance_ai\ml_models\train_model.py
cd ..
```

### Alternate script wrappers

```powershell
python .\scripts\train_expense_model.py
python .\scripts\train_anomaly_model.py
```

These wrappers now call the shared ML workflow service and save artifacts using their current filenames.

## FastAPI Endpoints

### Health

- `GET /health`

### Model status

- `GET /api/v1/models/status`

### Train model

- `POST /api/v1/models/train`

Example body:

```json
{
  "model_name": "loan_approval",
  "persist_model": true,
  "load_after_train": true
}
```

### Load model

- `POST /api/v1/models/load`

Example body:

```json
{
  "model_name": "loan_approval",
  "force_reload": false
}
```

### Save loaded model

- `POST /api/v1/models/save`

Example body:

```json
{
  "model_name": "loan_approval"
}
```

### Predict

- `POST /api/v1/predict`

The API accepts both original column names and snake_case field names.

Example body:

```json
{
  "ApplicantIncome": 5000,
  "CoapplicantIncome": 1500,
  "LoanAmount": 120,
  "Credit_History": 1
}
```

Postman-friendly example:

```json
{
  "applicant_income": 5000,
  "coapplicant_income": 1500,
  "loan_amount": 120,
  "credit_history": 1
}
```

## Postman Testing

Use:

- Method: `POST`
- URL: `http://localhost:8000/api/v1/predict`
- Header: `Content-Type: application/json`

Sample response shape:

```json
{
  "status": "success",
  "message": "Prediction generated successfully",
  "data": {
    "prediction": "Approved",
    "probability_approved": 0.84
  }
}
```

## Checks And Tests

Project checks:

```powershell
.\scripts\run-tests.ps1
```

Focused backend test:

```powershell
cd backend
.\venv\Scripts\python.exe -m unittest tests.test_fastapi_ml_api -v
cd ..
```

## Ports

Common local ports:

- Pyramid backend: `6543`
- FastAPI ML API: `8000`
- React frontend: `5173`

To inspect active ports:

```powershell
Get-NetTCPConnection -State Listen | Sort-Object LocalPort | Select-Object LocalAddress, LocalPort, OwningProcess
```

## Notes

- The original Pyramid backend was not replaced.
- FastAPI was added as a separate ML API layer for REST usage and later deployment.
- Model artifacts are stored locally and loaded from disk.
- The FastAPI layer is designed to be tested directly from Swagger UI or Postman.
