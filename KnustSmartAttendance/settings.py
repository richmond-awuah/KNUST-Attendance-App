"""
Django settings for KnustSmartAttendance project.
"""

from pathlib import Path
import os  # Import os for path handling

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# --- CORE SECURITY SETTINGS ---

# WARNING: Keep the secret key used in production secret!
# REPLACE THIS WITH A REAL SECRET KEY IN PRODUCTION
SECRET_KEY = 'django-insecure-h1#%h02%xi#fax$5ot%'

# Set DEBUG to False for security on a public server
DEBUG = False

# Allows connection from the public Render/Heroku address (Set to '*' for initial deployment)
ALLOWED_HOSTS = ['*']


# --- INSTALLED APPLICATIONS ---

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Your Application
    'core',
]


# --- MIDDLEWARE ---

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Ensure this matches your project name
ROOT_URLCONF = 'KnustSmartAttendance.urls'


# --- TEMPLATES ---

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

WSGI_APPLICATION = 'KnustSmartAttendance.wsgi.application'


# --- DATABASE CONFIGURATION ---
# Using default SQLite for local development and initial deployment
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# --- AUTHENTICATION ---

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


# --- INTERNATIONALIZATION ---

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# --- STATIC FILES (CSS, JavaScript, Images) ---

# This MUST be defined ONCE.
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# List of folders where Django will look for static files during development
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]


# --- DEFAULT PRIMARY KEY FIELD ---

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
