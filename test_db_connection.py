#!/usr/bin/env python
"""
Standalone database connection tester for SQL Server.
Can be run independently without Django dependencies.
"""

import os
import sys
import logging
import socket
import time
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_connection_params() -> Dict[str, Any]:
    """Get database connection parameters from environment."""
    return {
        'server': os.getenv('DATABASE_HOST', 'db'),
        'port': int(os.getenv('DATABASE_PORT', '1433')),
        'database': os.getenv('DATABASE_NAME', 'timesheet_prod'),
        'username': os.getenv('DATABASE_USER', 'sa'),
        'password': os.getenv('DATABASE_PASSWORD', 'YourStrong!Passw0rd'),
        'driver': 'ODBC Driver 18 for SQL Server'
    }


def test_network_connectivity(server: str, port: int, timeout: int = 10) -> bool:
    """Test basic network connectivity to SQL Server."""
    logger.info(f"Testing network connectivity to {server}:{port}...")
    
    try:
        # Test DNS resolution
        ip = socket.gethostbyname(server)
        logger.info(f"✓ DNS resolution: {server} -> {ip}")
    except socket.gaierror as e:
        logger.error(f"✗ DNS resolution failed: {e}")
        return False
    
    try:
        # Test port connectivity
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((server, port))
        sock.close()
        
        if result == 0:
            logger.info(f"✓ Port {port} is accessible")
            return True
        else:
            logger.error(f"✗ Port {port} is not accessible (error code: {result})")
            return False
            
    except Exception as e:
        logger.error(f"✗ Network connectivity test failed: {e}")
        return False


def check_pyodbc_availability():
    """Check if pyodbc is available and list drivers."""
    logger.info("Checking pyodbc availability...")
    
    try:
        import pyodbc
        logger.info("✓ pyodbc is available")
        
        drivers = pyodbc.drivers()
        logger.info(f"Available ODBC drivers: {drivers}")
        
        required_driver = 'ODBC Driver 18 for SQL Server'
        if required_driver in drivers:
            logger.info(f"✓ Required driver '{required_driver}' found")
            return True
        else:
            logger.error(f"✗ Required driver '{required_driver}' not found")
            logger.error("Available drivers don't include the required SQL Server driver")
            return False
            
    except ImportError:
        logger.error("✗ pyodbc is not installed or not available")
        return False
    except Exception as e:
        logger.error(f"✗ Error checking pyodbc: {e}")
        return False


def test_raw_sql_connection(params: Dict[str, Any]) -> bool:
    """Test raw SQL Server connection using pyodbc."""
    logger.info("Testing raw SQL Server connection...")
    
    try:
        import pyodbc
    except ImportError:
        logger.error("✗ pyodbc not available for connection test")
        return False
    
    # Build connection string
    conn_str = (
        f"DRIVER={{{params['driver']}}};"
        f"SERVER={params['server']},{params['port']};"
        f"DATABASE={params['database']};"
        f"UID={params['username']};"
        f"PWD={params['password']};"
        f"TrustServerCertificate=yes;"
        f"Encrypt=no;"
        f"Connection Timeout=30;"
    )
    
    logger.info("Attempting connection...")
    logger.info(f"Server: {params['server']}:{params['port']}")
    logger.info(f"Database: {params['database']}")
    logger.info(f"User: {params['username']}")
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT 1 as test, @@VERSION as version")
        result = cursor.fetchone()
        
        if result:
            logger.info(f"✓ Connection successful!")
            logger.info(f"Test query result: {result[0]}")
            logger.info(f"SQL Server version: {result[1][:100]}...")  # Truncate version string
            
            cursor.close()
            conn.close()
            return True
        else:
            logger.error("✗ Connection established but test query failed")
            return False
            
    except Exception as e:
        logger.error(f"✗ Connection failed: {e}")
        return False


def test_django_settings():
    """Test Django settings loading and database configuration."""
    logger.info("Testing Django settings...")
    
    try:
        # Set Django settings module
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'familyhub_timesheet.settings.production')
        
        import django
        from django.conf import settings
        
        if not settings.configured:
            django.setup()
        
        # Check database configuration
        db_config = settings.DATABASES['default']
        logger.info("✓ Django settings loaded successfully")
        logger.info(f"Database engine: {db_config['ENGINE']}")
        logger.info(f"Database host: {db_config['HOST']}")
        logger.info(f"Database port: {db_config['PORT']}")
        logger.info(f"Database name: {db_config['NAME']}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Django settings test failed: {e}")
        return False


def test_django_connection():
    """Test Django database connection."""
    logger.info("Testing Django database connection...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'familyhub_timesheet.settings.production')
        
        import django
        django.setup()
        
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            
        if result and result[0] == 1:
            logger.info("✓ Django database connection successful")
            return True
        else:
            logger.error("✗ Django database connection test query failed")
            return False
            
    except Exception as e:
        logger.error(f"✗ Django database connection failed: {e}")
        return False


def wait_for_database(max_attempts: int = 30, delay: int = 2) -> bool:
    """Wait for database to become available."""
    logger.info(f"Waiting for database (max {max_attempts} attempts, {delay}s intervals)...")
    
    params = get_connection_params()
    
    for attempt in range(1, max_attempts + 1):
        logger.info(f"Attempt {attempt}/{max_attempts}")
        
        # Test network connectivity first
        if test_network_connectivity(params['server'], params['port']):
            # If network is good, try database connection
            if test_raw_sql_connection(params):
                logger.info("✓ Database is ready!")
                return True
        
        if attempt < max_attempts:
            logger.info(f"Database not ready, waiting {delay} seconds...")
            time.sleep(delay)
    
    logger.error(f"✗ Database did not become available after {max_attempts * delay} seconds")
    return False


def run_comprehensive_test():
    """Run comprehensive database connectivity test."""
    logger.info("=" * 60)
    logger.info("SQL SERVER CONNECTION COMPREHENSIVE TEST")
    logger.info("=" * 60)
    
    # Environment info
    logger.info(f"Hostname: {socket.gethostname()}")
    logger.info(f"Python version: {sys.version}")
    
    if os.path.exists('/.dockerenv'):
        logger.info("Environment: Docker container")
    else:
        logger.info("Environment: Host system")
    
    logger.info("-" * 60)
    
    # Get connection parameters
    params = get_connection_params()
    logger.info("Connection parameters:")
    for key, value in params.items():
        if 'password' in key.lower():
            logger.info(f"  {key}: {'*' * len(str(value))}")
        else:
            logger.info(f"  {key}: {value}")
    
    logger.info("-" * 60)
    
    # Run tests
    tests = [
        ("Network Connectivity", lambda: test_network_connectivity(params['server'], params['port'])),
        ("PyODBC Availability", check_pyodbc_availability),
        ("Raw SQL Connection", lambda: test_raw_sql_connection(params)),
        ("Django Settings", test_django_settings),
        ("Django Connection", test_django_connection),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} Test ---")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"✗ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Database connection is fully operational.")
        return True
    else:
        logger.error("❌ Some tests failed. Review the output above for details.")
        return False


def main():
    """Main function for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='SQL Server connection tester')
    parser.add_argument('--wait', action='store_true', 
                       help='Wait for database to become available')
    parser.add_argument('--network-only', action='store_true',
                       help='Test only network connectivity')
    parser.add_argument('--full', action='store_true',
                       help='Run comprehensive test suite')
    parser.add_argument('--health-check', action='store_true',
                       help='Quick health check (for container health check)')
    
    args = parser.parse_args()
    
    if args.wait:
        success = wait_for_database()
        sys.exit(0 if success else 1)
    
    elif args.network_only:
        params = get_connection_params()
        success = test_network_connectivity(params['server'], params['port'])
        sys.exit(0 if success else 1)
    
    elif args.health_check:
        params = get_connection_params()
        network_ok = test_network_connectivity(params['server'], params['port'])
        if network_ok and check_pyodbc_availability():
            connection_ok = test_raw_sql_connection(params)
            sys.exit(0 if connection_ok else 1)
        else:
            sys.exit(1)
    
    elif args.full:
        success = run_comprehensive_test()
        sys.exit(0 if success else 1)
    
    else:
        # Default: basic test
        logger.info("Running basic connection test...")
        params = get_connection_params()
        network_ok = test_network_connectivity(params['server'], params['port'])
        if network_ok:
            connection_ok = test_raw_sql_connection(params)
            sys.exit(0 if connection_ok else 1)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
