# PowerShell script to run the Internship Analytics app
Write-Host "Stopping any existing Streamlit processes..." -ForegroundColor Yellow

# Kill any existing Streamlit processes
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like "*streamlit*" } | Stop-Process -Force
Get-Process streamlit -ErrorAction SilentlyContinue | Stop-Process -Force

# Kill any processes using port 8505
$connections = netstat -ano | findstr :8505
if ($connections) {
    Write-Host "Found connections on port 8505, waiting for cleanup..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
}

Write-Host "Starting Internship Analytics App..." -ForegroundColor Green
Set-Location "C:\Users\sunil\Desktop\Internship_Demand_Analytics"
python -m streamlit run app.py