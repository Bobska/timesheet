"""
Database utilities for SQL Server connection testing and management.
Provides comprehensive tools for debugging database connectivity issues.
"""

import os
import sys
import time
import socket
import logging
from typing import Dict, Any, Optional, Tuple
import subprocess
from contextlib import contextmanager

try:
    import pyodbc
    HAS_PYODBC = True
except ImportError:
    HAS_PYODBC = False

try:
    from django.conf import settings
    from django.db import connection
    from django.core.management import execute_from_command_line
    HAS_DJANGO = True
except ImportError:
    HAS_DJANGO = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseConnectionTester:
    """Comprehensive database connection testing utilities."""
    
    def __init__(self):
        self.connection_params = self._get_connection_params()
        
    def _get_connection_params(self) -> Dict[str, Any]:
        """Extract connection parameters from environment or defaults."""
        return {
            'server': os.getenv('DATABASE_HOST', 'db'),
            'port': int(os.getenv('DATABASE_PORT', '1433')),
            'database': os.getenv('DATABASE_NAME', 'timesheet_prod'),
            'username': os.getenv('DATABASE_USER', 'sa'),
            'password': os.getenv('DATABASE_PASSWORD', 'YourStrong!Passw0rd'),
            'driver': 'ODBC Driver 18 for SQL Server',
            'trust_certificate': 'yes',
            'encrypt': 'no'  # For local development
        }
    
    def test_network_connectivity(self) -> bool:
        """Test basic network connectivity to SQL Server."""
        logger.info("Testing network connectivity...")
        
        try:
            # Test DNS resolution
            socket.gethostbyname(self.connection_params['server'])
            logger.info(f"✓ DNS resolution successful for {self.connection_params['server']}")
        except socket.gaierror as e:
            logger.error(f"✗ DNS resolution failed: {e}")
            return False
        
        try:
            # Test port connectivity
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((
                self.connection_params['server'], 
                self.connection_params['port']
            ))
            sock.close()
            
            if result == 0:
                logger.info(f"✓ Port {self.connection_params['port']} is accessible")
                return True
            else:
                logger.error(f"✗ Port {self.connection_params['port']} is not accessible")
                return False
                
        except Exception as e:
            logger.error(f"✗ Network connectivity test failed: {e}")
            return False
    
    def check_odbc_drivers(self) -> bool:
        """Check if required ODBC drivers are installed."""
        logger.info("Checking ODBC drivers...")
        
        if not HAS_PYODBC:
            logger.error("✗ pyodbc is not installed")
            return False
        
        try:
            drivers = pyodbc.drivers()
            logger.info(f"Available ODBC drivers: {drivers}")
            
            if self.connection_params['driver'] in drivers:
                logger.info(f"✓ Required driver '{self.connection_params['driver']}' found")
                return True
            else:
                logger.error(f"✗ Required driver '{self.connection_params['driver']}' not found")
                return False
                
        except Exception as e:
            logger.error(f"✗ Error checking ODBC drivers: {e}")
            return False
    
    def test_raw_connection(self) -> bool:
        """Test raw pyodbc connection to SQL Server."""
        logger.info("Testing raw pyodbc connection...")
        
        if not HAS_PYODBC:
            logger.error("✗ pyodbc is not available")
            return False
        
        connection_strings = self._get_connection_strings()
        
        for i, conn_str in enumerate(connection_strings, 1):
            logger.info(f"Trying connection string {i}/{len(connection_strings)}...")
            try:
                conn = pyodbc.connect(conn_str, timeout=30)
                cursor = conn.cursor()
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if result and result[0] == 1:
                    logger.info(f"✓ Raw connection successful with string {i}")
                    return True
                    
            except Exception as e:
                logger.warning(f"✗ Connection string {i} failed: {e}")
                continue
        
        logger.error("✗ All connection strings failed")
        return False
    
    def _get_connection_strings(self):
        """Generate multiple connection string variations to try."""
        params = self.connection_params
        base_params = f"DRIVER={{{params['driver']}}};SERVER={params['server']},{params['port']};UID={params['username']};PWD={params['password']}"
        
        return [
            # Standard connection with database
            f"{base_params};DATABASE={params['database']};TrustServerCertificate={params['trust_certificate']};Encrypt={params['encrypt']};",
            
            # Without specifying database
            f"{base_params};TrustServerCertificate={params['trust_certificate']};Encrypt={params['encrypt']};",
            
            # With encryption enabled
            f"{base_params};DATABASE={params['database']};TrustServerCertificate={params['trust_certificate']};Encrypt=yes;",
            
            # Alternative server format
            f"DRIVER={{{params['driver']}}};SERVER=tcp:{params['server']},{params['port']};UID={params['username']};PWD={params['password']};DATABASE={params['database']};TrustServerCertificate={params['trust_certificate']};Encrypt={params['encrypt']};",
            
            # With connection timeout
            f"{base_params};DATABASE={params['database']};TrustServerCertificate={params['trust_certificate']};Encrypt={params['encrypt']};Connection Timeout=30;",
        ]
    
    def test_django_connection(self) -> bool:
        """Test Django database connection."""
        logger.info("Testing Django database connection...")
        
        if not HAS_DJANGO:
            logger.error("✗ Django is not available")
            return False
        
        try:
            # Configure Django settings
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'familyhub_timesheet.settings.production')
                import django
                django.setup()
            
            # Test connection
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                
            if result and result[0] == 1:
                logger.info("✓ Django database connection successful")
                return True
            else:
                logger.error("✗ Django database connection failed")
                return False
                
        except Exception as e:
            logger.error(f"✗ Django database connection error: {e}")
            return False
    
    def test_database_operations(self) -> bool:
        """Test basic database operations."""
        logger.info("Testing database operations...")
        
        try:
            if not HAS_DJANGO:
                logger.warning("Django not available, skipping database operations test")
                return True
                
            # Configure Django settings
            if not settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'familyhub_timesheet.settings.production')
                import django
                django.setup()
            
            from django.db import connection
            
            # Test table creation capability
            with connection.cursor() as cursor:
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='test_connection' AND xtype='U')
                    CREATE TABLE test_connection (id INT PRIMARY KEY, test_value NVARCHAR(50))
                """)
                
                # Test insert
                cursor.execute("INSERT INTO test_connection (id, test_value) VALUES (1, 'test')")
                
                # Test select
                cursor.execute("SELECT test_value FROM test_connection WHERE id = 1")
                result = cursor.fetchone()
                
                # Cleanup
                cursor.execute("DROP TABLE test_connection")
                
            if result and result[0] == 'test':
                logger.info("✓ Database operations test successful")
                return True
            else:
                logger.error("✗ Database operations test failed")
                return False
                
        except Exception as e:
            logger.error(f"✗ Database operations test error: {e}")
            return False
    
    def wait_for_database(self, max_attempts: int = 30, delay: int = 2) -> bool:
        """Wait for database to become available with retry logic."""
        logger.info(f"Waiting for database (max {max_attempts} attempts, {delay}s delay)...")
        
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Attempt {attempt}/{max_attempts}")
            
            if self.test_network_connectivity() and self.test_raw_connection():
                logger.info("✓ Database is ready!")
                return True
            
            if attempt < max_attempts:
                logger.info(f"Database not ready, waiting {delay} seconds...")
                time.sleep(delay)
        
        logger.error("✗ Database did not become available within timeout")
        return False
    
    def run_full_diagnostic(self) -> Dict[str, bool]:
        """Run comprehensive database connectivity diagnostic."""
        logger.info("=" * 50)
        logger.info("SQL Server Connection Diagnostic")
        logger.info("=" * 50)
        
        results = {}
        
        # Test steps
        tests = [
            ('Network Connectivity', self.test_network_connectivity),
            ('ODBC Drivers', self.check_odbc_drivers),
            ('Raw Connection', self.test_raw_connection),
            ('Django Connection', self.test_django_connection),
            ('Database Operations', self.test_database_operations),
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n--- {test_name} ---")
            try:
                results[test_name] = test_func()
            except Exception as e:
                logger.error(f"✗ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        # Summary
        logger.info("\n" + "=" * 50)
        logger.info("DIAGNOSTIC SUMMARY")
        logger.info("=" * 50)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            logger.info(f"{test_name}: {status}")
        
        logger.info(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! Database connection is working properly.")
        else:
            logger.error("❌ Some tests failed. Check the logs above for details.")
        
        return results


def check_container_environment():
    """Check if we're running in a Docker container and log environment info."""
    logger.info("Container Environment Check:")
    logger.info(f"Hostname: {socket.gethostname()}")
    logger.info(f"Platform: {sys.platform}")
    
    # Check if we're in Docker
    if os.path.exists('/.dockerenv'):
        logger.info("✓ Running in Docker container")
    else:
        logger.info("- Not running in Docker container")
    
    # Log relevant environment variables
    env_vars = ['DATABASE_HOST', 'DATABASE_PORT', 'DATABASE_NAME', 'DATABASE_USER', 'DATABASE_PASSWORD']
    for var in env_vars:
        value = os.getenv(var, 'Not set')
        if 'PASSWORD' in var and value != 'Not set':
            value = '*' * len(value)  # Mask password
        logger.info(f"{var}: {value}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Database connection testing utility')
    parser.add_argument('--health-check', action='store_true', help='Run health check (exit code based)')
    parser.add_argument('--wait', action='store_true', help='Wait for database to become available')
    parser.add_argument('--full', action='store_true', help='Run full diagnostic')
    
    args = parser.parse_args()
    
    check_container_environment()
    tester = DatabaseConnectionTester()
    
    if args.health_check:
        # Health check mode - exit with appropriate code
        success = tester.test_network_connectivity() and tester.test_raw_connection()
        sys.exit(0 if success else 1)
    
    elif args.wait:
        # Wait mode
        success = tester.wait_for_database()
        sys.exit(0 if success else 1)
    
    elif args.full:
        # Full diagnostic mode
        results = tester.run_full_diagnostic()
        success = all(results.values())
        sys.exit(0 if success else 1)
    
    else:
        # Default: run basic connectivity test
        logger.info("Running basic connectivity test...")
        success = tester.test_network_connectivity() and tester.test_raw_connection()
        sys.exit(0 if success else 1)
