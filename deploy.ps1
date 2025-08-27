# FamilyHub Timesheet - Production Deployment Script (PowerShell)
# This script sets up and deploys the timesheet application in production mode

param(
    [switch]$SkipPrompts
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 FamilyHub Timesheet - Production Deployment" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

# Check if Docker is installed
try {
    docker --version | Out-Null
    Write-Host "✅ Docker found" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    Write-Host "Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check if Docker Compose is available
try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose found" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Docker Compose is not available." -ForegroundColor Red
    exit 1
}

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    
    # Generate a secret key using Python
    try {
        $secretKey = python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
        
        # Update the .env file with the generated secret key
        $envContent = Get-Content ".env" -Raw
        $envContent = $envContent -replace "your-secret-key-here-change-this-to-a-random-string", $secretKey
        Set-Content ".env" $envContent
        
        Write-Host "✅ .env file created with generated secret key" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Warning: Could not generate secret key automatically." -ForegroundColor Yellow
        Write-Host "Please manually update the SECRET_KEY in .env file" -ForegroundColor Yellow
    }
    
    if (-not $SkipPrompts) {
        Write-Host "📝 Please review and update .env file if needed before continuing" -ForegroundColor Yellow
        Read-Host "Press Enter to continue after reviewing .env file"
    }
}

# Create logs directory
Write-Host "📁 Creating logs directory..." -ForegroundColor Yellow
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

# Build and start services
Write-Host "🔨 Building Docker images..." -ForegroundColor Yellow
docker-compose build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Failed to build Docker images" -ForegroundColor Red
    exit 1
}

Write-Host "🚀 Starting services..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Failed to start services" -ForegroundColor Red
    exit 1
}

# Wait for database to be ready
Write-Host "⏳ Waiting for SQL Server to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check if database is ready
Write-Host "🔍 Checking database connection..." -ForegroundColor Yellow
docker-compose exec web python manage.py check --database default --settings=familyhub_timesheet.settings.production

# Create database if it doesn't exist
Write-Host "🗄️  Creating database..." -ForegroundColor Yellow
docker-compose exec db /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "YourStrong!Passw0rd" -Q "IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'timesheet_prod') CREATE DATABASE timesheet_prod;"

# Run migrations
Write-Host "🔄 Running database migrations..." -ForegroundColor Yellow
docker-compose exec web python manage.py migrate --settings=familyhub_timesheet.settings.production

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Database migration failed" -ForegroundColor Red
    exit 1
}

# Collect static files
Write-Host "📦 Collecting static files..." -ForegroundColor Yellow
docker-compose exec web python manage.py collectstatic --noinput --settings=familyhub_timesheet.settings.production

# Create cache table
Write-Host "💾 Creating cache table..." -ForegroundColor Yellow
docker-compose exec web python manage.py createcachetable --settings=familyhub_timesheet.settings.production

# Create superuser
if (-not $SkipPrompts) {
    Write-Host "👤 Creating superuser..." -ForegroundColor Yellow
    Write-Host "Please create a superuser account for admin access:" -ForegroundColor Cyan
    docker-compose exec web python manage.py createsuperuser --settings=familyhub_timesheet.settings.production
}

Write-Host ""
Write-Host "🎉 Deployment complete!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host "📱 Application URL: http://localhost:8080" -ForegroundColor Cyan
Write-Host "🔐 Admin Panel: http://localhost:8080/admin/" -ForegroundColor Cyan
Write-Host "📊 Health Check: http://localhost:8080/" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Useful commands:" -ForegroundColor Yellow
Write-Host "   View logs: docker-compose logs -f" -ForegroundColor White
Write-Host "   Stop services: docker-compose down" -ForegroundColor White
Write-Host "   Restart services: docker-compose restart" -ForegroundColor White
Write-Host "   View running containers: docker-compose ps" -ForegroundColor White
Write-Host ""
Write-Host "✅ Your FamilyHub Timesheet is now running in production mode!" -ForegroundColor Green

# Open browser
if (-not $SkipPrompts) {
    $openBrowser = Read-Host "Would you like to open the application in your default browser? (Y/n)"
    if ($openBrowser -eq "" -or $openBrowser -eq "Y" -or $openBrowser -eq "y") {
        Start-Process "http://localhost:8080"
    }
}
