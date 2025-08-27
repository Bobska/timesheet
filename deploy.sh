#!/bin/bash

# FamilyHub Timesheet - Production Deployment Script
# This script sets up and deploys the timesheet application in production mode

set -e  # Exit on any error

echo "🚀 FamilyHub Timesheet - Production Deployment"
echo "=============================================="

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    
    # Generate a secret key
    SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
    
    # Update the .env file with the generated secret key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/your-secret-key-here-change-this-to-a-random-string/$SECRET_KEY/g" .env
    else
        # Linux
        sed -i "s/your-secret-key-here-change-this-to-a-random-string/$SECRET_KEY/g" .env
    fi
    
    echo "✅ .env file created with generated secret key"
    echo "📝 Please review and update .env file if needed before continuing"
    echo ""
    read -p "Press Enter to continue after reviewing .env file..."
fi

# Create logs directory
echo "📁 Creating logs directory..."
mkdir -p logs

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for SQL Server to be ready..."
sleep 30

# Check if database is ready
echo "🔍 Checking database connection..."
docker-compose exec web python manage.py check --database default --settings=familyhub_timesheet.settings.production

# Create database if it doesn't exist
echo "🗄️  Creating database..."
docker-compose exec db /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "YourStrong!Passw0rd" -Q "IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'timesheet_prod') CREATE DATABASE timesheet_prod;"

# Run migrations
echo "🔄 Running database migrations..."
docker-compose exec web python manage.py migrate --settings=familyhub_timesheet.settings.production

# Collect static files
echo "📦 Collecting static files..."
docker-compose exec web python manage.py collectstatic --noinput --settings=familyhub_timesheet.settings.production

# Create cache table
echo "💾 Creating cache table..."
docker-compose exec web python manage.py createcachetable --settings=familyhub_timesheet.settings.production

# Create superuser
echo "👤 Creating superuser..."
echo "Please create a superuser account for admin access:"
docker-compose exec web python manage.py createsuperuser --settings=familyhub_timesheet.settings.production

echo ""
echo "🎉 Deployment complete!"
echo "=============================================="
echo "📱 Application URL: http://localhost:8080"
echo "🔐 Admin Panel: http://localhost:8080/admin/"
echo "📊 Health Check: http://localhost:8080/"
echo ""
echo "📋 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart services: docker-compose restart"
echo "   View running containers: docker-compose ps"
echo ""
echo "✅ Your FamilyHub Timesheet is now running in production mode!"
