@echo off
echo Stopping any existing Streamlit processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq streamlit*" 2>nul
taskkill /F /IM streamlit.exe 2>nul

echo Waiting for port to be released...
timeout /t 2 /nobreak >nul

echo Starting Internship Analytics App...
cd /d C:\Users\sunil\Desktop\Internship_Demand_Analytics
python -m streamlit run app.py

pause