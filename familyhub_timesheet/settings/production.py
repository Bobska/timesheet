"""
Production Django settings for familyhub_timesheet project.
This file contains comprehensive SQL Server configuration with debugging and retry logic.
"""

import os
import logging
import structlog
from decouple import config
from .base import *
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# Allowed hosts
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,0.0.0.0,*').split(',')

# Enhanced Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            '()': structlog.stdlib.ProcessorFormatter,
            'processor': structlog.dev.ConsoleRenderer(colors=False),
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'db_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/database.log',
            'formatter': 'json',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console', 'db_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'mssql': {
            'handlers': ['console', 'db_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'pyodbc': {
            'handlers': ['console', 'db_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'familyhub_timesheet': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Database Configuration with Enhanced SQL Server Support
DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': config('DATABASE_NAME', default='timesheet_prod'),
        'USER': config('DATABASE_USER', default='sa'),
        'PASSWORD': config('DATABASE_PASSWORD', default='YourStrong!Passw0rd'),
        'HOST': config('DATABASE_HOST', default='db'),
        'PORT': config('DATABASE_PORT', default='1433'),
        'OPTIONS': {
            'driver': 'ODBC Driver 18 for SQL Server',
            'extra_params': ';'.join([
                'TrustServerCertificate=yes',
                'Encrypt=no',  # For local development
                'Connection Timeout=30',
                'Command Timeout=60',
                'Login Timeout=30',
                'MultipleActiveResultSets=True',
                'ApplicationIntent=ReadWrite',
                'ConnectRetryCount=3',
                'ConnectRetryInterval=10',
            ]),
        },
        'CONN_MAX_AGE': 600,  # Connection pooling - 10 minutes
        'CONN_HEALTH_CHECKS': True,
        'AUTOCOMMIT': True,
    }
}

# Fallback Database Configuration (SQLite for emergencies)
ENABLE_DATABASE_FALLBACK = config('ENABLE_DATABASE_FALLBACK', default=True, cast=bool)

if ENABLE_DATABASE_FALLBACK:
    DATABASES['sqlite_fallback'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/app/data/db_fallback.sqlite3',
    }

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# SSL/HTTPS settings (uncomment when using HTTPS)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# CSRF settings
CSRF_COOKIE_HTTPONLY = True
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8080',
    'http://127.0.0.1:8080',
]

# Session settings
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net")
CSP_SCRIPT_SRC = ("'self'", "https://cdn.jsdelivr.net")
CSP_IMG_SRC = ("'self'", "data:")
CSP_FONT_SRC = ("'self'", "https://cdn.jsdelivr.net")

# Static files configuration for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/django.log',
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
        }
    },
    'root': {
        'handlers': ['console'],
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'timesheet': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
import os
os.makedirs('/app/logs', exist_ok=True)

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@familyhub.com')

# Admin configuration
ADMINS = [
    ('Admin', config('ADMIN_EMAIL', default='admin@familyhub.com')),
]
MANAGERS = ADMINS

# Cache configuration for production
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
    }
}

# Performance optimizations
USE_TZ = True
USE_I18N = True

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5 MB
FILE_UPLOAD_PERMISSIONS = 0o644
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5 MB
