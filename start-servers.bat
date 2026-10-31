@echo off
TITLE WorkforceIQ Launcher
echo ==========================================================
echo  WorkforceIQ - Starting Platform Servers
echo ==========================================================

REM Start FastAPI Backend
start "WorkforceIQ Backend (FastAPI)" cmd /k "cd /d "%~dp0backend" && set PYTHONPATH=%~dp0;%~dp0backend && venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

REM Start React + Vite Frontend
start "WorkforceIQ Frontend (Vite)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Servers launched:
echo - Frontend UI:   http://localhost:5173
echo - Backend API:  http://127.0.0.1:8000
echo - Swagger Docs: http://127.0.0.1:8000/docs
echo.
pause
