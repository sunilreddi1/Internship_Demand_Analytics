@echo off
echo Stopping any existing Streamlit processes...
taskkill /f /im python.exe /fi "WINDOWTITLE eq streamlit*" >nul 2>&1
taskkill /f /im streamlit.exe >nul 2>&1

echo Waiting for port to be released...
timeout /t 3 /nobreak >nul

echo Starting Internship Analytics App...
cd /d "C:\Users\sunil\Desktop\Internship_Demand_Analytics"
python -m streamlit run app.py --server.headless true --server.port 8505

pause