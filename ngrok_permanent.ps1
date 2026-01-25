# PowerShell script for permanent ngrok tunnel with automatic cleanup
Write-Host "🌐 Starting ngrok tunnel with automatic cleanup..." -ForegroundColor Green

# Kill existing ngrok processes
Write-Host "🧹 Cleaning up existing ngrok processes..." -ForegroundColor Yellow
Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

Write-Host "🚀 Starting ngrok tunnel on port 8503..." -ForegroundColor Green
Write-Host "🔗 Public URL will be displayed below" -ForegroundColor Cyan
Write-Host "🌐 Web Interface: http://127.0.0.1:4040" -ForegroundColor Cyan
Write-Host "❌ Press Ctrl+C to stop the tunnel" -ForegroundColor Red
Write-Host ""

# Start ngrok
.\ngrok.exe http 8503