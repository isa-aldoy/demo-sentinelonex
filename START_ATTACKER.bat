@echo off
title ATTACKER APP - Port 7860
echo ========================================
echo SentinelOneX V4.0 - ATTACKER APP
echo ========================================
echo.
echo Starting Attacker on Port 7860...
echo.
echo IMPORTANT: Keep this window open!
echo The app will run here. Do NOT close this window.
echo.
echo Browser will auto-open to: http://127.0.0.1:7860
echo.
cd /d "%~dp0"
streamlit run attacker_streamlit.py --server.port 7860 --server.headless true
echo.
echo App stopped. Press any key to close...
pause
