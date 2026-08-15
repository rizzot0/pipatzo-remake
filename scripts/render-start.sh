#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-backend}"
export FRONTEND_DIST="${FRONTEND_DIST:-frontend/dist}"

exec uvicorn api.main_sqlite:app --host 0.0.0.0 --port "${PORT:-8000}"
