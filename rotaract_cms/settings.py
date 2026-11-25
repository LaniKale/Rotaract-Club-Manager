"""Django settings for the Rotaract Club Management System (Django 6.1)."""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Values that differ between your laptop and the live server are read from
# environment variables. On your laptop nothing needs setting: the defaults below
# are for development. On PythonAnywhere they are set in the WSGI file.

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-xc-#47@(*pk=%ks4#7(2j+o+0=lirxv$_64&z2b=@p#(%ovu))')

# DEBUG is on unless DJANGO_DEBUG is set to 0 (as it is on the live server).
DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'

# '*' lets phones on the same Wi-Fi reach your laptop while testing.
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

# Forms (including login) posted over HTTPS must come from a trusted address.
CSRF_TRUSTED_ORIGINS = ['https://*.pythonanywhere.com', 'https://*.app.github.dev']
# PythonAnywhere handles HTTPS in front of Django and says so in this header,
# so QR code links are generated as https://.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'members',
    'events',
    'attendance',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'members.middleware.ForcePasswordChangeMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rotaract_cms.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'members.context_processors.pending_applications',
            ],
        },
    },
]

WSGI_APPLICATION = 'rotaract_cms.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Jamaica'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
# `python manage.py collectstatic` copies every CSS/JS file here for the web server.
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Uploaded files (event flyers)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --- Rotaract CMS settings ---
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
AUTHENTICATION_BACKENDS = ['members.backends.EmailOrUsernameBackend']
# Members stay logged in on their phone for 30 days, so scanning the QR code is one tap.
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30


# How long a meeting's QR code stays valid after attendance is started.
QR_CODE_VALID_HOURS = 3

# Default primary key field type
# https://docs.djangoproject.com/en/6.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
