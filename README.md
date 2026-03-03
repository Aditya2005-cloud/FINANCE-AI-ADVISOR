# FINANCE-AI-ADVISOR

AI-powered finance advisor project with a Pyramid backend, ML prediction endpoints, and a React frontend workflow.

## Features

- Loan approval prediction API (`/api/predict`) using a trained scikit-learn pipeline.
- Prediction history API (`/api/predictions`) persisted in SQLite.
- AI financial file analysis API (`/api/ai/analyze`) for CSV/Excel/JSON/TXT uploads.
- Follow-up advisor chat API (`/api/ai/chat`) with session-based context.
- Local utility scripts for backend/frontend startup and project checks.

## Installation

### 1) Clone repository

```powershell
git clone <YOUR_GITHUB_REPO_URL>
cd FINANCE-AI-ADVISOR
```

### 2) Backend setup (Python)

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
cd ..
```

### 3) React frontend setup (Node.js)

```powershell
cd frontend
npm install
cd ..
```

## How To Run

### Run backend only

```powershell
.\scripts\start-backend.ps1
```

Backend default URL: `http://localhost:6543`

### Run React frontend only

```powershell
.\scripts\start-frontend.ps1
```

Frontend default URL: `http://localhost:5173`

### Run both

```powershell
.\scripts\start-all.ps1
```

## How To See Which Port Is Running

### Option 1: Use startup logs

- Backend script prints: `Starting backend on http://localhost:6543`
- Frontend script prints: `Starting frontend on http://localhost:5173`

### Option 2: Check active listening ports in PowerShell

```powershell
Get-NetTCPConnection -State Listen | Sort-Object LocalPort | Select-Object LocalAddress, LocalPort, OwningProcess
```

### Option 3: Check specific ports

```powershell
netstat -ano | findstr :6543
netstat -ano | findstr :5173
```

## Training (new pipeline)

The active model file used by prediction APIs is:

- `backend/finance_ai/ml_models/model.pkl`

To retrain and overwrite this model:

```powershell
cd backend
.\venv\Scripts\python.exe .\finance_ai\ml_models\train_model.py
cd ..
```

Notes:

- This training pipeline reads `backend/finance_ai/ml_models/loan_status_prediction.csv`.
- Placeholder scripts exist at `scripts/train_expense_model.py` and `scripts/train_anomaly_model.py`; implement these if you want separate production pipelines.

## React frontend

The repo scripts expect a React app in `frontend/` (typically Vite-based):

- `scripts/start-frontend.ps1` runs `npm run dev` (default Vite port `5173`)
- `scripts/run-tests.ps1` runs frontend lint and build commands

If `frontend/` is missing, create it first:

```powershell
npm create vite@latest frontend -- --template react
cd frontend
npm install
```
