# FINANCE-AI-ADVISOR

AI-powered finance advisor project with a Pyramid backend, ML prediction endpoints, and a React frontend workflow.
<img width="1281" height="733" alt="{52FC3C71-9483-4BAE-9340-D22CA12F0B29}" src="https://github.com/user-attachments/assets/26490c5c-3a05-4b5a-aa97-c5dda9566940" />
<img width="1145" height="644" alt="{A6361EA5-4B7F-48B7-B2B8-FBA997C9120B}" src="https://github.com/user-attachments/assets/3412c6ba-191f-4a64-9c1e-974411427c30" />
<img width="1158" height="479" alt="{2BD89FB3-AD02-47C7-A909-D8471A0FBDEB}" src="https://github.com/user-attachments/assets/3d88ab42-7adc-49b9-9987-cea4f27ba825" />
<img width="1113" height="432" alt="{F3EFBBAE-884F-4EB8-AF3C-4BB1DD95C9A9}" src="https://github.com/user-attachments/assets/87ea6bd9-e524-4509-b7db-36cc67d4e1bf" />
<img width="534" height="501" alt="{431767CB-3519-45A5-BB73-C42245D587E2}" src="https://github.com/user-attachments/assets/323dde64-43a3-4708-a569-360ae679e24d" />
<img width="534" height="501" alt="{431767CB-3519-45A5-BB73-C42245D587E2}" src="https://github.com/user-attachments/assets/323dde64-43a3-4708-a569-360ae679e24d" />


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
