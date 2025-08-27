# FamilyHub Timesheet - Production Management Script (PowerShell)
# This script provides common management operations for the production deployment

param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    
    [Parameter(Position=1)]
    [string]$Option = ""
)

$ErrorActionPreference = "Stop"

function Show-Help {
    Write-Host "FamilyHub Timesheet - Production Management" -ForegroundColor Green
    Write-Host "===========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: .\manage_production.ps1 [COMMAND]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Yellow
    Write-Host "  start           Start all services" -ForegroundColor White
    Write-Host "  stop            Stop all services" -ForegroundColor White
    Write-Host "  restart         Restart all services" -ForegroundColor White
    Write-Host "  status          Show service status" -ForegroundColor White
    Write-Host "  logs            Show service logs (use -f for follow)" -ForegroundColor White
    Write-Host "  shell           Open Django shell" -ForegroundColor White
    Write-Host "  dbshell         Open database shell" -ForegroundColor White
    Write-Host "  migrate         Run database migrations" -ForegroundColor White
    Write-Host "  collectstatic   Collect static files" -ForegroundColor White
    Write-Host "  createsuperuser Create Django superuser" -ForegroundColor White
    Write-Host "  backup-db       Backup database" -ForegroundColor White
    Write-Host "  restore-db      Restore database from backup" -ForegroundColor White
    Write-Host "  update          Update application (git pull + rebuild)" -ForegroundColor White
    Write-Host "  clean           Clean up Docker resources" -ForegroundColor White
    Write-Host "  health          Check application health" -ForegroundColor White
    Write-Host "  help            Show this help message" -ForegroundColor White
    Write-Host ""
}

function Test-Docker {
    try {
        docker --version | Out-Null
        docker-compose --version | Out-Null
    } catch {
        Write-Host "❌ Error: Docker or Docker Compose is not available." -ForegroundColor Red
        exit 1
    }
}

switch ($Command.ToLower()) {
    "start" {
        Write-Host "🚀 Starting FamilyHub Timesheet services..." -ForegroundColor Green
        Test-Docker
        docker-compose up -d
        Write-Host "✅ Services started. Access at http://localhost:8080" -ForegroundColor Green
    }
    
    "stop" {
        Write-Host "🛑 Stopping FamilyHub Timesheet services..." -ForegroundColor Yellow
        Test-Docker
        docker-compose down
        Write-Host "✅ Services stopped." -ForegroundColor Green
    }
    
    "restart" {
        Write-Host "🔄 Restarting FamilyHub Timesheet services..." -ForegroundColor Yellow
        Test-Docker
        docker-compose restart
        Write-Host "✅ Services restarted." -ForegroundColor Green
    }
    
    "status" {
        Write-Host "📊 Service Status:" -ForegroundColor Cyan
        Test-Docker
        docker-compose ps
    }
    
    "logs" {
        Write-Host "📋 Service Logs:" -ForegroundColor Cyan
        Test-Docker
        if ($Option -eq "-f") {
            docker-compose logs -f
        } else {
            docker-compose logs --tail=100
        }
    }
    
    "shell" {
        Write-Host "🐍 Opening Django shell..." -ForegroundColor Cyan
        Test-Docker
        docker-compose exec web python manage.py shell --settings=familyhub_timesheet.settings.production
    }
    
    "dbshell" {
        Write-Host "🗄️  Opening database shell..." -ForegroundColor Cyan
        Test-Docker
        docker-compose exec db /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "YourStrong!Passw0rd"
    }
    
    "migrate" {
        Write-Host "🔄 Running database migrations..." -ForegroundColor Yellow
        Test-Docker
        docker-compose exec web python manage.py migrate --settings=familyhub_timesheet.settings.production
        Write-Host "✅ Migrations completed." -ForegroundColor Green
    }
    
    "collectstatic" {
        Write-Host "📦 Collecting static files..." -ForegroundColor Yellow
        Test-Docker
        docker-compose exec web python manage.py collectstatic --noinput --settings=familyhub_timesheet.settings.production
        Write-Host "✅ Static files collected." -ForegroundColor Green
    }
    
    "createsuperuser" {
        Write-Host "👤 Creating superuser..." -ForegroundColor Cyan
        Test-Docker
        docker-compose exec web python manage.py createsuperuser --settings=familyhub_timesheet.settings.production
    }
    
    "backup-db" {
        Write-Host "💾 Creating database backup..." -ForegroundColor Yellow
        Test-Docker
        $backupFile = "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').bak"
        docker-compose exec db /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "YourStrong!Passw0rd" -Q "BACKUP DATABASE timesheet_prod TO DISK = '/var/opt/mssql/data/$backupFile'"
        Write-Host "✅ Database backup created: $backupFile" -ForegroundColor Green
    }
    
    "restore-db" {
        Write-Host "🔄 Restoring database from backup..." -ForegroundColor Yellow
        Write-Host "Available backup files:" -ForegroundColor Cyan
        docker-compose exec db find /var/opt/mssql/data -name "backup_*.bak" -type f
        Write-Host ""
        $backupFile = Read-Host "Enter backup filename"
        if ($backupFile) {
            Test-Docker
            docker-compose exec db /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "YourStrong!Passw0rd" -Q "RESTORE DATABASE timesheet_prod FROM DISK = '/var/opt/mssql/data/$backupFile' WITH REPLACE"
            Write-Host "✅ Database restored from: $backupFile" -ForegroundColor Green
        } else {
            Write-Host "❌ No backup file specified." -ForegroundColor Red
        }
    }
    
    "update" {
        Write-Host "🔄 Updating application..." -ForegroundColor Yellow
        git pull origin main
        Test-Docker
        docker-compose build
        docker-compose up -d
        docker-compose exec web python manage.py migrate --settings=familyhub_timesheet.settings.production
        docker-compose exec web python manage.py collectstatic --noinput --settings=familyhub_timesheet.settings.production
        Write-Host "✅ Application updated and redeployed." -ForegroundColor Green
    }
    
    "clean" {
        Write-Host "🧹 Cleaning up Docker resources..." -ForegroundColor Yellow
        Test-Docker
        docker-compose down --remove-orphans
        docker system prune -f
        Write-Host "✅ Docker resources cleaned up." -ForegroundColor Green
    }
    
    "health" {
        Write-Host "🏥 Checking application health..." -ForegroundColor Cyan
        Test-Docker
        
        Write-Host "Checking web service..." -ForegroundColor Yellow
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8080/" -TimeoutSec 10 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ Web service is healthy" -ForegroundColor Green
            } else {
                Write-Host "❌ Web service returned status code: $($response.StatusCode)" -ForegroundColor Red
            }
        } catch {
            Write-Host "❌ Web service is not responding" -ForegroundColor Red
        }
        
        Write-Host "Checking database connection..." -ForegroundColor Yellow
        try {
            docker-compose exec web python manage.py check --database default --settings=familyhub_timesheet.settings.production 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Database connection is healthy" -ForegroundColor Green
            } else {
                Write-Host "❌ Database connection failed" -ForegroundColor Red
            }
        } catch {
            Write-Host "❌ Database connection failed" -ForegroundColor Red
        }
    }
    
    default {
        Show-Help
    }
}
