@echo off
echo 🚀 Starting Internship Analytics App with Public Access...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start Streamlit in new window
echo Starting Streamlit app in new window...
start "Streamlit App" cmd /k "streamlit run app.py"

REM Wait for Streamlit to start
echo Waiting for Streamlit to initialize...
timeout /t 3 /nobreak > nul

REM Start ngrok tunnel
echo Starting ngrok tunnel...
echo Your public URL will appear below!
echo.
ngrok http 8501

pause