@echo off
echo 🚀 Deploying to Railway...
echo.

REM Check if Railway CLI is installed
railway --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Railway CLI...
    npm install -g @railway/cli
)

REM Login to Railway
echo Logging in to Railway...
railway login

REM Initialize project
echo Initializing Railway project...
railway init

REM Deploy
echo Deploying...
railway up

echo.
echo ✅ Deployment complete!
echo Check your Railway dashboard for the live URL.