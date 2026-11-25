@echo off
title SaigonStar Hotel - Web Khach Hang (Port 5173)
chcp 65001 >nul
echo ========================================================
echo  KHOI DONG WEB KHACH HANG (PORT 5173)
echo ========================================================
cd /d %~dp0frontend
call npm run dev -- --port 5173
pause
