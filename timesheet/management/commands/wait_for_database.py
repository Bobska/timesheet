"""
Django management command to wait for database availability.
Useful for container orchestration and startup scripts.
Usage: python manage.py wait_for_database
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connections
import time
import sys


class Command(BaseCommand):
    help = 'Wait for database to become available'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--database',
            type=str,
            default='default',
            help='Database alias to wait for (default: default)'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=60,
            help='Maximum time to wait in seconds (default: 60)'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=2,
            help='Check interval in seconds (default: 2)'
        )
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Suppress output except for errors'
        )
    
    def handle(self, *args, **options):
        database_alias = options['database']
        timeout = options['timeout']
        interval = options['interval']
        quiet = options['quiet']
        
        max_attempts = timeout // interval
        
        if not quiet:
            self.stdout.write(f"Waiting for database '{database_alias}' to become available...")
            self.stdout.write(f"Timeout: {timeout}s, Check interval: {interval}s")
        
        for attempt in range(1, max_attempts + 1):
            if not quiet:
                self.stdout.write(f"Attempt {attempt}/{max_attempts}")
            
            try:
                connection = connections[database_alias]
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                
                if result and result[0] == 1:
                    if not quiet:
                        self.stdout.write(
                            self.style.SUCCESS(f"Database '{database_alias}' is available!")
                        )
                    return
                    
            except Exception as e:
                if not quiet:
                    self.stdout.write(f"Connection failed: {e}")
            
            if attempt < max_attempts:
                if not quiet:
                    self.stdout.write(f"Waiting {interval} seconds...")
                time.sleep(interval)
        
        # If we get here, the database never became available
        error_msg = f"Database '{database_alias}' did not become available within {timeout} seconds"
        self.stdout.write(self.style.ERROR(error_msg))
        raise CommandError(error_msg)
