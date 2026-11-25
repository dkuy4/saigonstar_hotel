@echo off
title SaigonStar Hotel - Khoi dong toan bo he thong
chcp 65001 >nul
echo ====================================================================
echo   KHOI DONG TOAN BO HE THONG KHACH SAN SAI GON STAR
echo ====================================================================
echo.
echo  1. Kiem tra & Khoi dong Oracle Database (Docker)
echo  2. Backend API (FastAPI)     : http://127.0.0.1:8000 (Docs: /docs)
echo  3. Web Khach Hang (Portal)   : http://localhost:5173
echo  4. Web Quan Tri (Admin)      : http://localhost:5174
echo.
echo ====================================================================

:: 1. Kiem tra Docker container Oracle
docker start oracle23ai >nul 2>&1

:: 2. Khoi dong Backend
echo [1/3] Dang khoi dong Backend API...
start "SaigonStar - Backend API" cmd /k "%~dp0run_backend.bat"

:: 3. Cho cho Backend san sang (Ping endpoint /health toi da 15s)
echo [2/3] Dang doi Backend API ket noi co so du lieu...
:wait_backend
powershell -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/health' -TimeoutSec 1; if ($r.status -eq 'healthy') { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    powershell -Command "Start-Sleep -Milliseconds 800"
    goto wait_backend
)
echo      - Backend API da san sang (Health OK)!

:: 4. Khoi dong Web Khach Hang
echo [3/3] Dang khoi dong Web Khach Hang & Web Admin...
start "SaigonStar - Web Khach Hang" cmd /k "%~dp0run_frontend_guest.bat"

:: 5. Khoi dong Web Admin
start "SaigonStar - Web Admin" cmd /k "%~dp0run_frontend_admin.bat"

echo.
echo ====================================================================
echo   TAT CA 3 DICH VU DA DUOC KHOI DONG DUNG THU TU VA CO DU LIEU!
echo   - Web Khach Hang : http://localhost:5173
echo   - Web Quan Tri   : http://localhost:5174
echo ====================================================================
timeout /t 5 >nul
exit
