# 🚀 Start Internship Analytics App with Public Access
Write-Host "🚀 Starting Internship Analytics App with Public Access..." -ForegroundColor Green
Write-Host ""

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Start Streamlit in background
Write-Host "Starting Streamlit app..." -ForegroundColor Yellow
Start-Job -ScriptBlock {
    & "streamlit" "run" "app.py"
} | Out-Null

# Wait for Streamlit to start
Write-Host "Waiting for Streamlit to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start ngrok tunnel
Write-Host "Starting ngrok tunnel..." -ForegroundColor Yellow
Write-Host "Your app will be publicly accessible via the ngrok URL shown below!" -ForegroundColor Green
Write-Host ""

# Run ngrok (this will block until user stops it)
ngrok http 8501