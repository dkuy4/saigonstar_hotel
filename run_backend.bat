@echo off
title SaigonStar Hotel - Backend API (Port 8000)
chcp 65001 >nul
echo ========================================================
echo  KHOI DONG BACKEND FASTAPI (PORT 8000)
echo ========================================================

:: Dam bao container Oracle dang bat
docker start oracle23ai >nul 2>&1

:: Giai phong port 8000 neu dang bi chiem dung
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

cd /d %~dp0backend

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

echo Backend dang chay tai http://127.0.0.1:8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
