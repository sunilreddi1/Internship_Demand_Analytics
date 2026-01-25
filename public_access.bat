@echo off
echo 🚀 Starting Internship Analytics App with Public Access...
echo.

echo 📱 Starting Streamlit app on port 8503...
start /B python -m streamlit run app.py --server.port 8503 --server.address 0.0.0.0 --server.headless true

echo ⏳ Waiting for app to start...
timeout /t 3 /nobreak > nul

echo 🌐 Starting ngrok tunnel...
start /B ngrok.exe http 8503

echo ⏳ Waiting for tunnel to establish...
timeout /t 5 /nobreak > nul

echo.
echo ✅ App is now running!
echo.
echo 🔗 Local Access: http://localhost:8503
echo 🌍 Public Access: Check ngrok output above for HTTPS URL
echo 📊 ngrok Dashboard: http://127.0.0.1:4040
echo.
echo Press Ctrl+C in the ngrok window to stop the tunnel
echo Press Ctrl+C in the Streamlit window to stop the app
echo.
pause