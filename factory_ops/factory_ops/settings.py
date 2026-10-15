"""
FactoryOps QC — Master Configuration Settings
Zapuza Technologies LLP | Python Django Developer Internship Assessment
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env located at BASE_DIR or current directory
BASE_DIR = Path(__file__).resolve().parent.parent

env_file = BASE_DIR / '.env'
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()

# Security & Environment Configuration
# Secret key: Read from environment; require in production, provide safe dynamic ephemeral key in dev
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or os.environ.get('SECRET_KEY')

DEBUG = (os.environ.get('DJANGO_DEBUG') or os.environ.get('DEBUG', 'False')).strip().lower() in ('true', '1', 'yes')

if not SECRET_KEY:
    if DEBUG:
        import secrets
        SECRET_KEY = secrets.token_urlsafe(50)
    else:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured(
            "CRITICAL: SECRET_KEY environment variable is missing in production mode. "
            "Please set DJANGO_SECRET_KEY or SECRET_KEY in your environment or .env file."
        )

# Allowed Hosts: Parse comma-separated host list safely
raw_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS') or os.environ.get('ALLOWED_HOSTS', '')
if raw_hosts:
    ALLOWED_HOSTS = [h.strip() for h in raw_hosts.split(',') if h.strip()]
elif DEBUG:
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
else:
    ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Factory Quality Control Modules (BRD Scope)
    'master_setup.apps.MasterSetupConfig',
    'calibration.apps.CalibrationConfig',
    'material_intake.apps.MaterialIntakeConfig',
    'inspection.apps.InspectionConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'factory_ops.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'master_setup.context_processors.rbac_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'factory_ops.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files (User-uploaded Mill Test Certificates)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
