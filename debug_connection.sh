#!/bin/bash
# Comprehensive database connection debugging script
# This script provides multiple debugging tools for SQL Server connectivity

set -e

echo "========================================"
echo "SQL Server Connection Debug Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "SUCCESS" ]; then
        echo -e "${GREEN}✓ $message${NC}"
    elif [ "$status" = "ERROR" ]; then
        echo -e "${RED}✗ $message${NC}"
    elif [ "$status" = "INFO" ]; then
        echo -e "${YELLOW}ℹ $message${NC}"
    else
        echo "$message"
    fi
}

# Get environment variables with defaults
DB_HOST="${DATABASE_HOST:-db}"
DB_PORT="${DATABASE_PORT:-1433}"
DB_NAME="${DATABASE_NAME:-timesheet_prod}"
DB_USER="${DATABASE_USER:-sa}"
DB_PASS="${DATABASE_PASSWORD:-YourStrong!Passw0rd}"

print_status "INFO" "Environment Configuration:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Password: $(echo $DB_PASS | sed 's/./*/g')"
echo ""

# Check if we're in Docker
if [ -f /.dockerenv ]; then
    print_status "INFO" "Running inside Docker container"
    echo "  Container hostname: $(hostname)"
else
    print_status "INFO" "Running on host system"
fi
echo ""

# 1. Basic network connectivity tests
echo "1. NETWORK CONNECTIVITY TESTS"
echo "----------------------------------------"

# DNS resolution test
print_status "INFO" "Testing DNS resolution for $DB_HOST..."
if nslookup $DB_HOST >/dev/null 2>&1; then
    resolved_ip=$(nslookup $DB_HOST | grep 'Address:' | tail -n1 | awk '{print $2}')
    print_status "SUCCESS" "DNS resolution successful: $DB_HOST -> $resolved_ip"
else
    print_status "ERROR" "DNS resolution failed for $DB_HOST"
fi

# Ping test (if ping is available)
if command -v ping >/dev/null 2>&1; then
    print_status "INFO" "Testing ping to $DB_HOST..."
    if ping -c 3 $DB_HOST >/dev/null 2>&1; then
        print_status "SUCCESS" "Ping successful to $DB_HOST"
    else
        print_status "ERROR" "Ping failed to $DB_HOST"
    fi
else
    print_status "INFO" "Ping command not available"
fi

# Port connectivity test
print_status "INFO" "Testing port connectivity to $DB_HOST:$DB_PORT..."
if command -v telnet >/dev/null 2>&1; then
    if timeout 10 bash -c "</dev/tcp/$DB_HOST/$DB_PORT" 2>/dev/null; then
        print_status "SUCCESS" "Port $DB_PORT is accessible on $DB_HOST"
    else
        print_status "ERROR" "Port $DB_PORT is not accessible on $DB_HOST"
    fi
elif command -v nc >/dev/null 2>&1; then
    if nc -z -w5 $DB_HOST $DB_PORT 2>/dev/null; then
        print_status "SUCCESS" "Port $DB_PORT is accessible on $DB_HOST (via nc)"
    else
        print_status "ERROR" "Port $DB_PORT is not accessible on $DB_HOST (via nc)"
    fi
else
    print_status "INFO" "Neither telnet nor nc available for port testing"
fi

echo ""

# 2. ODBC Driver tests
echo "2. ODBC DRIVER TESTS"
echo "----------------------------------------"

# Check if odbcinst is available
if command -v odbcinst >/dev/null 2>&1; then
    print_status "INFO" "Checking installed ODBC drivers..."
    odbcinst -q -d
    
    if odbcinst -q -d | grep -q "ODBC Driver 18 for SQL Server"; then
        print_status "SUCCESS" "ODBC Driver 18 for SQL Server is installed"
    else
        print_status "ERROR" "ODBC Driver 18 for SQL Server is NOT installed"
        print_status "INFO" "Available drivers:"
        odbcinst -q -d | sed 's/^/    /'
    fi
else
    print_status "INFO" "odbcinst command not available"
fi

# Check for ODBC libraries
print_status "INFO" "Checking for ODBC library files..."
if [ -f "/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.*.so" ]; then
    print_status "SUCCESS" "Microsoft ODBC libraries found"
    ls -la /opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.*.so
else
    print_status "ERROR" "Microsoft ODBC libraries not found"
fi

echo ""

# 3. Python environment tests
echo "3. PYTHON ENVIRONMENT TESTS"
echo "----------------------------------------"

print_status "INFO" "Python version: $(python --version)"

# Check Python packages
print_status "INFO" "Checking Python packages..."
packages=("django" "pyodbc" "mssql-django")
for package in "${packages[@]}"; do
    if python -c "import $package" 2>/dev/null; then
        version=$(python -c "import $package; print(getattr($package, '__version__', 'unknown'))" 2>/dev/null || echo "unknown")
        print_status "SUCCESS" "$package is installed (version: $version)"
    else
        print_status "ERROR" "$package is NOT installed"
    fi
done

echo ""

# 4. SQL Server connection tests
echo "4. SQL SERVER CONNECTION TESTS"
echo "----------------------------------------"

# Test with Python script
if python -c "import pyodbc" 2>/dev/null; then
    print_status "INFO" "Running Python connection test..."
    
    cat > /tmp/test_connection.py << 'EOF'
import pyodbc
import os
import sys

# Get connection parameters
server = os.getenv('DATABASE_HOST', 'db')
port = os.getenv('DATABASE_PORT', '1433')
database = os.getenv('DATABASE_NAME', 'timesheet_prod')
username = os.getenv('DATABASE_USER', 'sa')
password = os.getenv('DATABASE_PASSWORD', 'YourStrong!Passw0rd')

# Build connection string
conn_str = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={server},{port};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    f"TrustServerCertificate=yes;"
    f"Encrypt=no;"
    f"Connection Timeout=30;"
)

try:
    print(f"Attempting connection to {server}:{port}")
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Test query
    cursor.execute("SELECT 1 as test, @@VERSION as version")
    result = cursor.fetchone()
    
    print(f"✓ Connection successful!")
    print(f"Test result: {result[0]}")
    print(f"SQL Server version: {result[1][:100]}...")
    
    cursor.close()
    conn.close()
    sys.exit(0)
    
except Exception as e:
    print(f"✗ Connection failed: {e}")
    sys.exit(1)
EOF
    
    if python /tmp/test_connection.py; then
        print_status "SUCCESS" "Python pyodbc connection test passed"
    else
        print_status "ERROR" "Python pyodbc connection test failed"
    fi
    
    rm -f /tmp/test_connection.py
else
    print_status "ERROR" "pyodbc not available for connection testing"
fi

echo ""

# 5. Django tests
echo "5. DJANGO TESTS"
echo "----------------------------------------"

if python -c "import django" 2>/dev/null; then
    print_status "INFO" "Running Django connection test..."
    
    # Set Django settings module
    export DJANGO_SETTINGS_MODULE="familyhub_timesheet.settings.production"
    
    # Test Django database connection
    if python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'familyhub_timesheet.settings.production')
django.setup()
from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT 1')
result = cursor.fetchone()
print('Django connection test:', 'SUCCESS' if result[0] == 1 else 'FAILED')
" 2>/dev/null; then
        print_status "SUCCESS" "Django database connection test passed"
    else
        print_status "ERROR" "Django database connection test failed"
    fi
else
    print_status "ERROR" "Django not available for testing"
fi

echo ""

# 6. Container networking tests (if in Docker)
if [ -f /.dockerenv ]; then
    echo "6. CONTAINER NETWORKING TESTS"
    echo "----------------------------------------"
    
    print_status "INFO" "Container network configuration:"
    
    # Show network interfaces
    if command -v ip >/dev/null 2>&1; then
        print_status "INFO" "Network interfaces:"
        ip addr show | grep -E '^[0-9]+:|inet ' | sed 's/^/    /'
    fi
    
    # Show routing table
    if command -v route >/dev/null 2>&1; then
        print_status "INFO" "Routing table:"
        route -n | sed 's/^/    /'
    fi
    
    # Test DNS resolution from container
    print_status "INFO" "DNS configuration:"
    if [ -f /etc/resolv.conf ]; then
        cat /etc/resolv.conf | sed 's/^/    /'
    fi
    
    echo ""
fi

# 7. Summary and recommendations
echo "7. SUMMARY AND RECOMMENDATIONS"
echo "----------------------------------------"

print_status "INFO" "If connection tests are failing, try these steps:"
echo "  1. Ensure SQL Server container is running: docker ps"
echo "  2. Check SQL Server logs: docker logs <sql-server-container>"
echo "  3. Verify network connectivity between containers"
echo "  4. Check firewall settings if running on separate hosts"
echo "  5. Verify SQL Server authentication mode allows SQL logins"
echo "  6. Test connection from SQL Server Management Studio if available"

echo ""
print_status "INFO" "Debugging script completed"
echo "========================================"
