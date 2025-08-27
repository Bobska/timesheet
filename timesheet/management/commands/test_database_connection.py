"""
Django management command to test and diagnose database connectivity.
Usage: python manage.py test_database_connection
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction
from django.conf import settings
import logging
import time
import sys

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test database connectivity and diagnose connection issues'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--database',
            type=str,
            default='default',
            help='Database alias to test (default: default)'
        )
        parser.add_argument(
            '--wait',
            action='store_true',
            help='Wait for database to become available'
        )
        parser.add_argument(
            '--max-attempts',
            type=int,
            default=30,
            help='Maximum number of connection attempts when waiting'
        )
        parser.add_argument(
            '--delay',
            type=int,
            default=2,
            help='Delay between connection attempts in seconds'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
        parser.add_argument(
            '--create-test-table',
            action='store_true',
            help='Create and test a temporary table'
        )
    
    def handle(self, *args, **options):
        database_alias = options['database']
        verbose = options['verbose']
        
        if verbose:
            self.stdout.write(self.style.SUCCESS('=== Database Connection Test ==='))
            self.stdout.write(f"Testing database: {database_alias}")
        
        # Check if database exists in settings
        if database_alias not in settings.DATABASES:
            raise CommandError(f"Database '{database_alias}' not found in settings")
        
        db_config = settings.DATABASES[database_alias]
        if verbose:
            self.stdout.write(f"Engine: {db_config['ENGINE']}")
            self.stdout.write(f"Host: {db_config.get('HOST', 'N/A')}")
            self.stdout.write(f"Port: {db_config.get('PORT', 'N/A')}")
            self.stdout.write(f"Database: {db_config.get('NAME', 'N/A')}")
        
        if options['wait']:
            success = self._wait_for_database(
                database_alias, 
                options['max_attempts'], 
                options['delay'],
                verbose
            )
            if not success:
                raise CommandError(f"Database '{database_alias}' did not become available")
        else:
            success = self._test_connection(database_alias, verbose)
            if not success:
                raise CommandError(f"Database '{database_alias}' connection failed")
        
        if options['create_test_table']:
            self._test_table_operations(database_alias, verbose)
        
        self.stdout.write(
            self.style.SUCCESS(f'Database "{database_alias}" connection successful!')
        )
    
    def _test_connection(self, database_alias, verbose=False):
        """Test basic database connection."""
        try:
            connection = connections[database_alias]
            
            if verbose:
                self.stdout.write("Testing basic connection...")
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                
            if result and result[0] == 1:
                if verbose:
                    self.stdout.write(self.style.SUCCESS("✓ Basic connection test passed"))
                return True
            else:
                if verbose:
                    self.stdout.write(self.style.ERROR("✗ Basic connection test failed"))
                return False
                
        except Exception as e:
            if verbose:
                self.stdout.write(
                    self.style.ERROR(f"✗ Connection failed: {e}")
                )
            return False
    
    def _wait_for_database(self, database_alias, max_attempts, delay, verbose=False):
        """Wait for database to become available."""
        if verbose:
            self.stdout.write(f"Waiting for database (max {max_attempts} attempts, {delay}s delay)...")
        
        for attempt in range(1, max_attempts + 1):
            if verbose:
                self.stdout.write(f"Attempt {attempt}/{max_attempts}")
            
            if self._test_connection(database_alias, verbose=False):
                if verbose:
                    self.stdout.write(self.style.SUCCESS("✓ Database is ready!"))
                return True
            
            if attempt < max_attempts:
                if verbose:
                    self.stdout.write(f"Database not ready, waiting {delay} seconds...")
                time.sleep(delay)
        
        if verbose:
            self.stdout.write(self.style.ERROR("✗ Database did not become available"))
        return False
    
    def _test_table_operations(self, database_alias, verbose=False):
        """Test table creation, insertion, and deletion."""
        if verbose:
            self.stdout.write("Testing table operations...")
        
        try:
            connection = connections[database_alias]
            
            with transaction.atomic(using=database_alias):
                with connection.cursor() as cursor:
                    # Create test table
                    if verbose:
                        self.stdout.write("Creating test table...")
                    
                    # Handle different database engines
                    if 'sqlite' in connection.vendor:
                        create_sql = """
                            CREATE TABLE IF NOT EXISTS test_connection_table (
                                id INTEGER PRIMARY KEY,
                                test_value TEXT
                            )
                        """
                    elif 'microsoft' in connection.vendor or 'mssql' in connection.vendor:
                        create_sql = """
                            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='test_connection_table' AND xtype='U')
                            CREATE TABLE test_connection_table (
                                id INT PRIMARY KEY,
                                test_value NVARCHAR(50)
                            )
                        """
                    else:
                        create_sql = """
                            CREATE TABLE IF NOT EXISTS test_connection_table (
                                id INT PRIMARY KEY,
                                test_value VARCHAR(50)
                            )
                        """
                    
                    cursor.execute(create_sql)
                    
                    # Insert test data
                    if verbose:
                        self.stdout.write("Inserting test data...")
                    
                    cursor.execute(
                        "INSERT INTO test_connection_table (id, test_value) VALUES (1, 'test')"
                    )
                    
                    # Query test data
                    if verbose:
                        self.stdout.write("Querying test data...")
                    
                    cursor.execute(
                        "SELECT test_value FROM test_connection_table WHERE id = 1"
                    )
                    result = cursor.fetchone()
                    
                    if result and result[0] == 'test':
                        if verbose:
                            self.stdout.write(self.style.SUCCESS("✓ Table operations test passed"))
                    else:
                        raise Exception("Test data query failed")
                    
                    # Clean up
                    if verbose:
                        self.stdout.write("Cleaning up test table...")
                    
                    cursor.execute("DROP TABLE test_connection_table")
                    
        except Exception as e:
            if verbose:
                self.stdout.write(
                    self.style.ERROR(f"✗ Table operations test failed: {e}")
                )
            raise CommandError(f"Table operations test failed: {e}")
    
    def _get_database_info(self, database_alias):
        """Get detailed database information."""
        try:
            connection = connections[database_alias]
            
            with connection.cursor() as cursor:
                # Try to get database version
                if 'sqlite' in connection.vendor:
                    cursor.execute("SELECT sqlite_version()")
                    version = cursor.fetchone()[0]
                    return f"SQLite {version}"
                elif 'microsoft' in connection.vendor or 'mssql' in connection.vendor:
                    cursor.execute("SELECT @@VERSION")
                    version = cursor.fetchone()[0]
                    return f"SQL Server: {version[:100]}..."
                else:
                    return f"Database vendor: {connection.vendor}"
                    
        except Exception:
            return "Database info unavailable"
