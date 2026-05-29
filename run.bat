@echo off
REM Starts backend (port 8080) and frontend (port 5173) in two windows.
start "OBSCURA backend"  cmd /k "cd backend && .venv\Scripts\activate && uvicorn app.main:app --reload --port 8080"
start "OBSCURA frontend" cmd /k "cd frontend && npm run dev"
echo Opening http://localhost:5173 ...
timeout /t 4 >nul
start http://localhost:5173
