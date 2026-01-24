# Stop any existing Streamlit processes
Write-Host "Stopping any existing Streamlit processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*streamlit*" -or $_.CommandLine -like "*app.py*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

# Wait for port to be released
Write-Host "Waiting for port to be released..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start the app
Write-Host "Starting Internship Analytics App..." -ForegroundColor Green
Set-Location "C:\Users\sunil\Desktop\Internship_Demand_Analytics"
& python -m streamlit run app.py --server.headless true --server.port 8505 --server.address 10.93.3.148 --server.sslCertFile certs/server.crt --server.sslKeyFile certs/server.key