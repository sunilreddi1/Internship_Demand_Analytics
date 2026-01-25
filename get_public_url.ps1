# 🚀 Simple Public URL Getter
Write-Host "🚀 Starting your Internship Analytics app..." -ForegroundColor Green
Write-Host ""

# Start Streamlit
Write-Host "📱 Starting Streamlit..." -ForegroundColor Yellow
Start-Process "streamlit" "run app.py --server.headless true"

# Wait for app to start
Write-Host "⏳ Waiting for app to load..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start ngrok
Write-Host "🌐 Creating public tunnel..." -ForegroundColor Yellow
Start-Process "ngrok" "http 8501"

# Wait for tunnel
Start-Sleep -Seconds 3

Write-Host "" -ForegroundColor Green
Write-Host "🎉 Check the ngrok window for your public URL!" -ForegroundColor Green
Write-Host "🌐 Look for: https://xxxxx.ngrok-free.app" -ForegroundColor Cyan
Write-Host "" -ForegroundColor Yellow
Write-Host "💡 The URL will appear in the ngrok terminal window" -ForegroundColor Gray