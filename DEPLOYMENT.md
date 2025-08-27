# FamilyHub Timesheet - Production Deployment Guide

## Overview

This guide covers the complete production deployment of the FamilyHub Timesheet application using Docker, SQL Server 2022, and running on port 8080.

## Architecture

- **Web Application**: Django 5.x with Gunicorn WSGI server
- **Database**: Microsoft SQL Server 2022 (Docker container)
- **Reverse Proxy**: Nginx (optional, for static file serving)
- **Containerization**: Docker and Docker Compose
- **Port Configuration**:
  - **Production Access**: http://localhost:8080
  - **Development**: http://localhost:8000-8010 (unchanged)
  - **Database**: Port 1433 (internal)

## Prerequisites

### Required Software

1. **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
   - Download from: https://www.docker.com/products/docker-desktop
   - Minimum version: 20.10+

2. **Docker Compose**
   - Usually included with Docker Desktop
   - For Linux: `sudo apt-get install docker-compose` or `sudo yum install docker-compose`

3. **Git** (for cloning and updates)
   - Download from: https://git-scm.com/downloads

### System Requirements

- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB free space for Docker containers and database
- **OS**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+, CentOS 7+)

## Quick Start

### 1. Clone and Navigate to Project

```bash
git clone https://github.com/Bobska/timesheet.git
cd timesheet
```

### 2. Run Deployment Script

**Linux/macOS:**
```bash
chmod +x deploy.sh
./deploy.sh
```

**Windows (PowerShell):**
```powershell
# If you have WSL or Git Bash
bash deploy.sh

# Or run commands manually (see Manual Deployment section)
```

### 3. Access Application

- **Main Application**: http://localhost:8080
- **Admin Panel**: http://localhost:8080/admin/
- **Health Check**: http://localhost:8080/

## Manual Deployment Steps

If the automated script doesn't work, follow these manual steps:

### 1. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your preferred editor
nano .env  # or vim .env, or code .env
```

**Required .env variables:**
```bash
SECRET_KEY=your-generated-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DATABASE_PASSWORD=YourStrong!Passw0rd
```

### 2. Generate Secret Key

```bash
# Python method
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Online generator (alternative)
# Visit: https://djecrety.ir/
```

### 3. Build and Start Services

```bash
# Build Docker images
docker-compose build

# Start services in background
docker-compose up -d

# Check service status
docker-compose ps
```

### 4. Database Setup

```bash
# Wait for SQL Server to start (30-60 seconds)
sleep 30

# Create database
docker-compose exec db /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "YourStrong!Passw0rd" -Q "IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'timesheet_prod') CREATE DATABASE timesheet_prod;"

# Run migrations
docker-compose exec web python manage.py migrate --settings=familyhub_timesheet.settings.production

# Create cache table
docker-compose exec web python manage.py createcachetable --settings=familyhub_timesheet.settings.production
```

### 5. Static Files and Admin User

```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput --settings=familyhub_timesheet.settings.production

# Create superuser
docker-compose exec web python manage.py createsuperuser --settings=familyhub_timesheet.settings.production
```

## Management Operations

### Using the Management Script

The `manage_production.sh` script provides convenient commands:

```bash
# Make script executable (Linux/macOS)
chmod +x manage_production.sh

# Show available commands
./manage_production.sh help

# Common operations
./manage_production.sh start      # Start services
./manage_production.sh stop       # Stop services
./manage_production.sh status     # Check status
./manage_production.sh logs       # View logs
./manage_production.sh logs -f    # Follow logs
```

### Manual Management Commands

```bash
# Service management
docker-compose start              # Start existing containers
docker-compose stop               # Stop containers
docker-compose restart            # Restart containers
docker-compose down               # Stop and remove containers

# View logs
docker-compose logs web           # Web application logs
docker-compose logs db            # Database logs
docker-compose logs -f            # Follow all logs

# Django management
docker-compose exec web python manage.py shell --settings=familyhub_timesheet.settings.production
docker-compose exec web python manage.py migrate --settings=familyhub_timesheet.settings.production
docker-compose exec web python manage.py collectstatic --noinput --settings=familyhub_timesheet.settings.production

# Database access
docker-compose exec db /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "YourStrong!Passw0rd"
```

## Configuration Details

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Django secret key | - | Yes |
| `DEBUG` | Debug mode | False | No |
| `ALLOWED_HOSTS` | Allowed hostnames | localhost,127.0.0.1 | No |
| `DATABASE_NAME` | Database name | timesheet_prod | No |
| `DATABASE_USER` | Database user | sa | No |
| `DATABASE_PASSWORD` | Database password | - | Yes |
| `DATABASE_HOST` | Database host | db | No |
| `DATABASE_PORT` | Database port | 1433 | No |

### Database Configuration

**Connection Details:**
- **Server**: SQL Server 2022 (Latest)
- **Database**: timesheet_prod
- **Authentication**: SQL Server Authentication
- **Username**: sa
- **Password**: YourStrong!Passw0rd (configurable)
- **Port**: 1433 (internal Docker network)

### Security Features

**Production Security Settings:**
- Debug mode disabled
- Secure cookie settings
- HSTS headers
- XSS protection
- Content type nosniff
- Frame denial
- CSRF protection

**Network Security:**
- Internal Docker network for service communication
- Only necessary ports exposed externally
- Rate limiting via Nginx (when enabled)

## Port Configuration

### External Access
- **Main Application**: Port 8080 → http://localhost:8080
- **Nginx (optional)**: Port 80 → http://localhost

### Internal Docker Network
- **Django/Gunicorn**: Port 8000
- **SQL Server**: Port 1433
- **Nginx**: Port 80

### Development Ports (Unchanged)
- **Django Dev Server**: 8000-8010
- **Database**: SQLite (file-based)

## Backup and Recovery

### Database Backup

```bash
# Create backup
./manage_production.sh backup-db

# Manual backup
docker-compose exec db /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "YourStrong!Passw0rd" -Q "BACKUP DATABASE timesheet_prod TO DISK = '/var/opt/mssql/data/backup_$(date +%Y%m%d).bak'"
```

### Database Recovery

```bash
# Restore from backup
./manage_production.sh restore-db

# Manual restore
docker-compose exec db /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "YourStrong!Passw0rd" -Q "RESTORE DATABASE timesheet_prod FROM DISK = '/var/opt/mssql/data/backup_filename.bak' WITH REPLACE"
```

### Volume Backup

```bash
# Create volume backup
docker run --rm -v timesheet_sqlserver_data:/data -v $(pwd):/backup alpine tar czf /backup/sqlserver_backup.tar.gz /data

# Restore volume backup
docker run --rm -v timesheet_sqlserver_data:/data -v $(pwd):/backup alpine tar xzf /backup/sqlserver_backup.tar.gz -C /
```

## Troubleshooting

### Common Issues

#### 1. Port 8080 Already in Use
```bash
# Check what's using the port
netstat -tulpn | grep 8080
# or
lsof -i :8080

# Stop the conflicting service or change port in docker-compose.yml
```

#### 2. Database Connection Failed
```bash
# Check if SQL Server container is running
docker-compose ps

# Check SQL Server logs
docker-compose logs db

# Test database connection
docker-compose exec web python manage.py check --database default --settings=familyhub_timesheet.settings.production
```

#### 3. Static Files Not Loading
```bash
# Recollect static files
docker-compose exec web python manage.py collectstatic --noinput --settings=familyhub_timesheet.settings.production

# Check Nginx configuration (if using)
docker-compose logs nginx
```

#### 4. Permission Denied Errors (Linux/macOS)
```bash
# Make scripts executable
chmod +x deploy.sh manage_production.sh

# Fix file ownership (if needed)
sudo chown -R $USER:$USER .
```

#### 5. Out of Memory
```bash
# Check Docker memory usage
docker stats

# Increase Docker memory allocation in Docker Desktop settings
# Or free up system memory
```

### Health Checks

```bash
# Application health
curl http://localhost:8080/

# Database connectivity
docker-compose exec web python manage.py check --database default --settings=familyhub_timesheet.settings.production

# Container health
docker-compose ps
```

### Log Locations

- **Application Logs**: `docker-compose logs web`
- **Database Logs**: `docker-compose logs db`
- **Nginx Logs**: `docker-compose logs nginx`
- **Django Logs**: `/app/logs/django.log` (inside container)

## Updating the Application

### Automated Update

```bash
./manage_production.sh update
```

### Manual Update

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose build

# Apply migrations
docker-compose exec web python manage.py migrate --settings=familyhub_timesheet.settings.production

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput --settings=familyhub_timesheet.settings.production

# Restart services
docker-compose restart
```

## Performance Optimization

### Recommended Settings

**For Production Use:**
- **CPU**: 2+ cores
- **RAM**: 4GB+ allocated to Docker
- **Storage**: SSD recommended for database performance

**Docker Compose Resource Limits:**
```yaml
services:
  web:
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
  
  db:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

### Monitoring

```bash
# Monitor resource usage
docker stats

# Monitor logs continuously
docker-compose logs -f

# Check disk usage
docker system df
```

## Security Considerations

### Network Security
- Internal Docker network isolates services
- Only necessary ports exposed externally
- Database not directly accessible from outside

### Application Security
- HTTPS ready (configure SSL certificates for production)
- CSRF protection enabled
- XSS protection headers
- Secure cookie settings

### Database Security
- Strong password required
- SQL Server authentication
- Encrypted connections (TrustServerCertificate for local dev)

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**:
   - Check logs for errors
   - Monitor disk usage
   - Backup database

2. **Monthly**:
   - Update base images
   - Review security settings
   - Clean up old Docker images

3. **Quarterly**:
   - Update dependencies
   - Review performance metrics
   - Test backup/restore procedures

### Getting Help

1. **Check logs first**: `docker-compose logs`
2. **Verify configuration**: Review `.env` file
3. **Test connectivity**: Use health check commands
4. **GitHub Issues**: Report bugs at repository

## Advanced Configuration

### Custom SSL/HTTPS Setup

To enable HTTPS, update the Nginx configuration and add SSL certificates:

```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/private.key;
    # ... rest of configuration
}
```

### External Database

To use an external SQL Server:

1. Update `.env` with external database details
2. Remove `db` service from `docker-compose.yml`
3. Update `depends_on` in web service

### Load Balancing

For high availability, consider:
- Multiple web containers
- External load balancer
- Database clustering
- Redis/Memcached for session storage

---

## Success Checklist

After deployment, verify:

- ✅ Services start without errors: `docker-compose ps`
- ✅ Application accessible: http://localhost:8080
- ✅ Admin panel works: http://localhost:8080/admin/
- ✅ Database connection successful: Migration commands work
- ✅ Static files load correctly: CSS/JS functional
- ✅ User registration/login works
- ✅ Time entries can be created and viewed
- ✅ Data persists after container restart

---

**Your FamilyHub Timesheet is now ready for production use! 🎉**
