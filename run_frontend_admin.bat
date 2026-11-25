@echo off
title SaigonStar Hotel - Web Admin Portal (Port 5174)
chcp 65001 >nul
echo ========================================================
echo  KHOI DONG WEB QUAN TRI NOI BO (PORT 5174)
echo  Khach san Sai Gon Star - Staff Portal (Le tan / Quan ly)
echo ========================================================

cd /d %~dp0frontend-admin

:: Kiem tra node_modules
if not exist node_modules (
    echo Dang cai dat thu vien npm cho Web Admin...
    call npm install
)

echo Web Admin dang khoi chay tai http://localhost:5174 ...
call npm run dev -- --port 5174
pause
