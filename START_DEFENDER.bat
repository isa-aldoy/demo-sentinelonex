@echo off
title DEFENDER APP - Port 7861
echo ========================================
echo SentinelOneX V4.0 - DEFENDER APP
echo ========================================
echo.
echo Starting Defender on Port 7861...
echo Setting API Key...
set GOOGLE_API_KEY=AIzaSyCbAr_gNaWJABhjMvaxcXXFdHL7h8YDo8Q
echo.
echo IMPORTANT: Keep this window open!
echo The app will run here. Do NOT close this window.
echo.
echo Browser will auto-open to: http://127.0.0.1:7861
echo.
cd /d "%~dp0"
streamlit run defender_streamlit.py --server.port 7861 --server.headless true
echo.
echo App stopped. Press any key to close...
pause
