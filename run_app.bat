@echo off
echo Stopping any existing Streamlit processes...

REM Kill Python processes running Streamlit
for /f "tokens=2" %%i in ('tasklist ^| findstr python') do (
    taskkill /PID %%i /F >nul 2>&1
)

REM Kill any streamlit processes
taskkill /F /IM streamlit.exe >nul 2>&1

echo Waiting for port to be released...
timeout /t 3 /nobreak >nul

echo Starting Internship Analytics App...
cd /d C:\Users\sunil\Desktop\Internship_Demand_Analytics
python -m streamlit run app.py

pause