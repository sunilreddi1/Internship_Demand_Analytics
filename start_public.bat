@echo off
echo 🚀 Starting Internship Analytics App with Public Access...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start Streamlit in background
echo Starting Streamlit app...
start /B streamlit run app.py

REM Wait a moment for Streamlit to start
timeout /t 5 /nobreak > nul

REM Start ngrok tunnel
echo Starting ngrok tunnel...
ngrok http 8501

REM Keep the window open
pause