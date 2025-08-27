"""
Database router for handling fallback database logic.
Routes queries to primary or fallback database based on availability.
"""

import logging
import time
from django.conf import settings

logger = logging.getLogger(__name__)


class DatabaseRouter:
    """
    Database router that handles primary/fallback database selection.
    """
    
    def __init__(self):
        self.last_primary_check = 0
        self.primary_available = None
        self.check_interval = 60  # Check every minute
    
    def _test_database_connection(self, database_alias):
        """Test if a database connection is working."""
        try:
            from django.db import connections
            
            conn = connections[database_alias]
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
            return result and result[0] == 1
            
        except Exception as e:
            logger.warning(f"Database connection test failed for {database_alias}: {e}")
            return False
    
    def _is_primary_available(self):
        """Check if primary database is available with caching."""
        current_time = time.time()
        
        # Use cached result if recent
        if (current_time - self.last_primary_check) < self.check_interval:
            return self.primary_available
        
        # Test primary database
        self.primary_available = self._test_database_connection('default')
        self.last_primary_check = current_time
        
        if self.primary_available:
            logger.info("Primary database is available")
        else:
            logger.warning("Primary database is not available")
        
        return self.primary_available
    
    def _get_target_database(self):
        """Determine which database to use."""
        # If fallback is disabled, always use primary
        if not getattr(settings, 'ENABLE_DATABASE_FALLBACK', False):
            return 'default'
        
        # Check if primary is available
        if self._is_primary_available():
            return 'default'
        
        # Check if fallback database exists in settings
        if 'sqlite_fallback' in settings.DATABASES:
            logger.info("Using fallback database")
            return 'sqlite_fallback'
        
        # No fallback available, use primary (will likely fail)
        logger.error("Primary database unavailable and no fallback configured")
        return 'default'
    
    def db_for_read(self, model, **hints):
        """Suggest database to read from."""
        return self._get_target_database()
    
    def db_for_write(self, model, **hints):
        """Suggest database to write to."""
        return self._get_target_database()
    
    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if models are in the same database."""
        db_set = {'default', 'sqlite_fallback'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure that certain models' migrations go to the right database."""
        # Allow migrations on both databases
        if db in {'default', 'sqlite_fallback'}:
            return True
        return False
