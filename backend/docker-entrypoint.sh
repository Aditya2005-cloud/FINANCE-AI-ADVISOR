#!/bin/sh
set -eu

APP_MODE="${APP_MODE:-pyramid}"

python - <<'PY'
from sqlalchemy import create_engine

from finance_ai.models import Base

engine = create_engine("sqlite:///finance_ai.db")
Base.metadata.create_all(bind=engine)
PY

case "$APP_MODE" in
  pyramid)
    exec pserve development.ini
    ;;
  fastapi)
    exec python -m uvicorn finance_ai.fastapi_app:app --host 0.0.0.0 --port 8000
    ;;
  *)
    echo "Unsupported APP_MODE: $APP_MODE" >&2
    echo "Use APP_MODE=pyramid or APP_MODE=fastapi" >&2
    exit 1
    ;;
esac
