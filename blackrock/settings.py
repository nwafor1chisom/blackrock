import os
from pathlib import Path
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-blackrock-change-this-in-production-use-env-var')

DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'blackrock-a5lc.onrender.com',
    '.onrender.com',
]


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'cloudinary_storage',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'cloudinary',
    # Local apps
    'core',
    'users',
    'wallet',
    'ledger',
    'transactions',
    'kyc',
    'dashboard',
    'payments',
    'referral',
    'adminpanel',
   
    
]

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': config('CLOUDINARY_API_KEY'),
    'API_SECRET': config('CLOUDINARY_API_SECRET'),
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'


MIDDLEWARE = [
    # Security (must be first)
    'django.middleware.security.SecurityMiddleware',

    # Static files handler (IMPORTANT for UI)
    'whitenoise.middleware.WhiteNoiseMiddleware',

    # Core Django middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # SaaS-level custom middleware (your logic)
    'core.middleware.PublicRouteGuard',
    'core.middleware.AuditLogMiddleware',
    'core.middleware.KYCEnforcementMiddleware',
]

ROOT_URLCONF = 'blackrock.urls'

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
                'core.context_processors.global_context',
            ],
        },
    },
]



WSGI_APPLICATION = 'blackrock.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=config(
            'DATABASE_URL',
            default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'
        ),
        conn_max_age=600,
        ssl_require=True  # ✅ Add this line
    )
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']  # top-level; app statics found via APP_DIRS
STATIC_ROOT = BASE_DIR / 'staticfiles'


MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


AUTH_USER_MODEL = 'users.User'

# OPTION B — SendGrid (recommended for production)
#   1. Sign up at sendgrid.com, create an API key
#   2. Set EMAIL_HOST = 'smtp.sendgrid.net'
#   3. Set EMAIL_HOST_USER = 'apikey'
#   4. Set EMAIL_HOST_PASSWORD = '<your-sendgrid-api-key>'


EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = config('SENDGRID_API_KEY', default='')
SENDGRID_SANDBOX_MODE_IN_DEBUG = False
DEFAULT_FROM_EMAIL = 'BlackRock Support <supportblackrock@gmail.com>'

# ── DEBUG (IMPORTANT FOR EMAIL TESTING) ──
DEBUG = config('DEBUG', default=False, cast=bool)

# MUST BE FALSE if you want real email sending
OTP_DEBUG_PRINT = False
# Security settings for production
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB


# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} [{name}] {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'otp': {
            'format': '[{asctime}] OTP {levelname}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'otp_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'otp',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'blackrock.audit': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'blackrock.otp': {
            'handlers': ['otp_console'],
            'level': 'DEBUG',   # DEBUG shows every OTP flow step in terminal
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'django.core.mail': {
            'handlers': ['console'],
            'level': 'DEBUG',   # Shows SMTP negotiation details
            'propagate': False,
        },
    },
}

# ── Public site settings ───────────────────────────────────────────────────
CONTACT_ADMIN_EMAIL = 'supportblackrock@gmail.com'  # receives contact form emails
WHATSAPP_NUMBER     = '18625967401'                  # international format, no +

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# ── Authentication redirects ──────────────────────────────────────────────
# LOGIN_URL: where @login_required sends unauthenticated users
LOGIN_URL          = '/users/login/'   # @login_required redirects here
# After login, default destination (overridden by ?next= param)
LOGIN_REDIRECT_URL = '/dashboard/'     # after login, go to dashboard
# After logout: go to '/' — home_view renders home.html, NO redirect loop
# LOGOUT_REDIRECT_URL intentionally omitted — logout_view in users/views.py handles all logout redirects
