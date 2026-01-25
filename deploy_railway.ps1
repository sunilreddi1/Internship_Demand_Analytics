# PowerShell script to deploy Internship Analytics to Railway
Write-Host "Deploying Internship Analytics to Railway..." -ForegroundColor Green

# Check if Railway CLI is installed
if (!(Get-Command railway -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Railway CLI..." -ForegroundColor Yellow
    npm install -g @railway/cli
}

# Login to Railway (if not already logged in)
Write-Host "Logging in to Railway..." -ForegroundColor Cyan
railway login

# Initialize Railway project
Write-Host "Initializing Railway project..." -ForegroundColor Cyan
railway init

# Set environment variables
Write-Host "Setting up environment variables..." -ForegroundColor Cyan
# Note: You'll need to set DATABASE_URL in Railway dashboard or via CLI
# railway variables set DATABASE_URL your_postgresql_url

# Deploy
Write-Host "Deploying to Railway..." -ForegroundColor Green
railway up

Write-Host "Deployment complete! Check your Railway dashboard for the app URL." -ForegroundColor Green