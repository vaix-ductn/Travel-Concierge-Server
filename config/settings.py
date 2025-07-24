"""
Django settings for travel concierge project.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-development-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']  # For development only

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'user_manager',  # User management app with authentication
    'travel_concierge',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'base.middleware.csrf_bypass.AgentCSRFBypassMiddleware',
    'base.middleware.csrf_bypass.CustomCsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
import pymysql
pymysql.install_as_MySQLdb()

# Database configuration for Cloud Run
if os.getenv('ENVIRONMENT') == 'production':
    # Production database (Cloud SQL)
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.mysql'),
            'NAME': os.getenv('DB_NAME', 'travel_concierge'),
            'USER': os.getenv('DB_USER', 'travel_concierge'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'TravelConcierge2024!'),
            'HOST': os.getenv('DB_HOST', '/cloudsql/travelapp-461806:us-central1:travel-concierge-db'),
            'PORT': os.getenv('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
            },
        }
    }
else:
    # Staging/Development database
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.mysql'),
            'NAME': os.getenv('DB_NAME', 'travel_concierge'),
            'USER': os.getenv('DB_USER', 'travel_concierge'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'TravelConcierge2024!'),
            'HOST': os.getenv('DB_HOST', '104.198.165.249'),  # Cloud SQL public IP
            'PORT': os.getenv('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'connect_timeout': 60,
                'read_timeout': 60,
                'write_timeout': 60,
            },
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# JWT Authentication settings
JWT_SECRET = os.getenv('JWT_SECRET', 'your-super-secret-jwt-key-here-change-in-production')
JWT_EXPIRATION = os.getenv('JWT_EXPIRATION', '24h')
BCRYPT_ROUNDS = int(os.getenv('BCRYPT_ROUNDS', '12'))

# Rate Limiting settings
LOGIN_RATE_LIMIT_ATTEMPTS = int(os.getenv('LOGIN_RATE_LIMIT_ATTEMPTS', '5'))
LOGIN_RATE_LIMIT_WINDOW = int(os.getenv('LOGIN_RATE_LIMIT_WINDOW', '900'))  # 15 minutes
ACCOUNT_LOCKOUT_DURATION = int(os.getenv('ACCOUNT_LOCKOUT_DURATION', '1800'))  # 30 minutes

# Cache configuration for rate limiting
# Use dummy cache for all environments to avoid Redis dependency
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# CORS settings
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '["http://localhost:3000"]')
if isinstance(CORS_ALLOWED_ORIGINS, str):
    import json
    CORS_ALLOWED_ORIGINS = json.loads(CORS_ALLOWED_ORIGINS)

# Force IPv4 to avoid IPv6 encoding issues
USE_IPV4 = True

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'user_manager.service.bearer_auth.BearerHeaderAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Changed from IsAuthenticated to AllowAny for profile APIs
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        # Temporarily disable throttling for staging
        # 'rest_framework.throttling.AnonRateThrottle',
        # 'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'profile': '100/15min',  # For profile GET/UPDATE endpoints
        'password_change': '5/15min',  # For password change endpoint
    }
}

# Disable Django admin login requirement for API documentation
LOGIN_URL = None
LOGIN_REDIRECT_URL = None

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/profile.log',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'travel_concierge': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'user_manager': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        # Suppress OpenTelemetry context warnings
        'opentelemetry': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'google.adk': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}