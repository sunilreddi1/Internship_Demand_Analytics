# 🚀 Railway Deployment Script

Write-Host "🚀 Deploying to Railway..." -ForegroundColor Green
Write-Host ""

# Check if Railway CLI is installed
try {
    $version = railway --version 2>$null
    Write-Host "Railway CLI found: $version" -ForegroundColor Green
} catch {
    Write-Host "Installing Railway CLI..." -ForegroundColor Yellow
    npm install -g @railway/cli
}

# Login to Railway
Write-Host "Logging in to Railway..." -ForegroundColor Yellow
railway login

# Initialize project
Write-Host "Initializing Railway project..." -ForegroundColor Yellow
railway init

# Deploy
Write-Host "Deploying..." -ForegroundColor Yellow
railway up

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "Check your Railway dashboard for the live URL."