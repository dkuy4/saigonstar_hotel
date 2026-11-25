@echo off
title SaigonStar Hotel - Web Khach Hang (Port 5173)
chcp 65001 >nul
echo ========================================================
echo  KHOI DONG WEB KHACH HANG (PORT 5173)
echo  Khach san Sai Gon Star - Dat phong truc tuyen
echo ========================================================

cd /d %~dp0frontend

:: Kiem tra node_modules
if not exist node_modules (
    echo Dang cai dat thu vien npm cho Web Khach Hang...
    call npm install
)

echo Web Khach Hang dang khoi chay tai http://localhost:5173 ...
call npm run dev -- --port 5173
pause
