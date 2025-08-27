#!/bin/bash

# FamilyHub Timesheet - Production Management Script
# This script provides common management operations for the production deployment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

show_help() {
    echo "FamilyHub Timesheet - Production Management"
    echo "=========================================="
    echo ""
    echo "Usage: ./manage_production.sh [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start           Start all services"
    echo "  stop            Stop all services"
    echo "  restart         Restart all services"
    echo "  status          Show service status"
    echo "  logs            Show service logs (use -f for follow)"
    echo "  shell           Open Django shell"
    echo "  dbshell         Open database shell"
    echo "  migrate         Run database migrations"
    echo "  collectstatic   Collect static files"
    echo "  createsuperuser Create Django superuser"
    echo "  backup-db       Backup database"
    echo "  restore-db      Restore database from backup"
    echo "  update          Update application (git pull + rebuild)"
    echo "  clean           Clean up Docker resources"
    echo "  health          Check application health"
    echo "  help            Show this help message"
    echo ""
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Error: Docker is not installed."
        exit 1
    fi
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Error: Docker Compose is not installed."
        exit 1
    fi
}

case "${1:-help}" in
    start)
        echo "🚀 Starting FamilyHub Timesheet services..."
        check_docker
        docker-compose up -d
        echo "✅ Services started. Access at http://localhost:8080"
        ;;
    
    stop)
        echo "🛑 Stopping FamilyHub Timesheet services..."
        check_docker
        docker-compose down
        echo "✅ Services stopped."
        ;;
    
    restart)
        echo "🔄 Restarting FamilyHub Timesheet services..."
        check_docker
        docker-compose restart
        echo "✅ Services restarted."
        ;;
    
    status)
        echo "📊 Service Status:"
        check_docker
        docker-compose ps
        ;;
    
    logs)
        echo "📋 Service Logs:"
        check_docker
        if [ "$2" = "-f" ]; then
            docker-compose logs -f
        else
            docker-compose logs --tail=100
        fi
        ;;
    
    shell)
        echo "🐍 Opening Django shell..."
        check_docker
        docker-compose exec web python manage.py shell --settings=familyhub_timesheet.settings.production
        ;;
    
    dbshell)
        echo "🗄️  Opening database shell..."
        check_docker
        docker-compose exec db /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "YourStrong!Passw0rd"
        ;;
    
    migrate)
        echo "🔄 Running database migrations..."
        check_docker
        docker-compose exec web python manage.py migrate --settings=familyhub_timesheet.settings.production
        echo "✅ Migrations completed."
        ;;
    
    collectstatic)
        echo "📦 Collecting static files..."
        check_docker
        docker-compose exec web python manage.py collectstatic --noinput --settings=familyhub_timesheet.settings.production
        echo "✅ Static files collected."
        ;;
    
    createsuperuser)
        echo "👤 Creating superuser..."
        check_docker
        docker-compose exec web python manage.py createsuperuser --settings=familyhub_timesheet.settings.production
        ;;
    
    backup-db)
        echo "💾 Creating database backup..."
        check_docker
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).bak"
        docker-compose exec db /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "YourStrong!Passw0rd" -Q "BACKUP DATABASE timesheet_prod TO DISK = '/var/opt/mssql/data/$BACKUP_FILE'"
        echo "✅ Database backup created: $BACKUP_FILE"
        ;;
    
    restore-db)
        echo "🔄 Restoring database from backup..."
        echo "Available backup files:"
        docker-compose exec db find /var/opt/mssql/data -name "backup_*.bak" -type f
        echo ""
        read -p "Enter backup filename: " BACKUP_FILE
        if [ -n "$BACKUP_FILE" ]; then
            check_docker
            docker-compose exec db /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "YourStrong!Passw0rd" -Q "RESTORE DATABASE timesheet_prod FROM DISK = '/var/opt/mssql/data/$BACKUP_FILE' WITH REPLACE"
            echo "✅ Database restored from: $BACKUP_FILE"
        else
            echo "❌ No backup file specified."
        fi
        ;;
    
    update)
        echo "🔄 Updating application..."
        git pull origin main
        check_docker
        docker-compose build
        docker-compose up -d
        docker-compose exec web python manage.py migrate --settings=familyhub_timesheet.settings.production
        docker-compose exec web python manage.py collectstatic --noinput --settings=familyhub_timesheet.settings.production
        echo "✅ Application updated and redeployed."
        ;;
    
    clean)
        echo "🧹 Cleaning up Docker resources..."
        check_docker
        docker-compose down --remove-orphans
        docker system prune -f
        echo "✅ Docker resources cleaned up."
        ;;
    
    health)
        echo "🏥 Checking application health..."
        check_docker
        echo "Checking web service..."
        if curl -f http://localhost:8080/ > /dev/null 2>&1; then
            echo "✅ Web service is healthy"
        else
            echo "❌ Web service is not responding"
        fi
        
        echo "Checking database connection..."
        if docker-compose exec web python manage.py check --database default --settings=familyhub_timesheet.settings.production > /dev/null 2>&1; then
            echo "✅ Database connection is healthy"
        else
            echo "❌ Database connection failed"
        fi
        ;;
    
    help|*)
        show_help
        ;;
esac
