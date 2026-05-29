#!/usr/bin/env bash
# Starts backend (8080) and frontend (5173). Ctrl+C stops both.
set -e
( cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8080 ) &
BACK=$!
( cd frontend && npm run dev ) &
FRONT=$!
trap "kill $BACK $FRONT" INT
wait
