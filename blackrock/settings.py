import os
from pathlib import Path
from decouple import Config, RepositoryEnv, AutoConfig


BASE_DIR = Path(__file__).resolve().parent.parent
env_file = os.path.join(BASE_DIR, ".env")

if os.path.exists(env_file):
    config = Config(RepositoryEnv(env_file))
else:
    config = AutoConfig()

SECRET_KEY = config('SECRET_KEY', default='django-insecure-blackrock-change-this-in-production-use-env-var')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
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

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # SaaS-level auth lock: authenticated users cannot access public routes
    'core.middleware.PublicRouteGuard',
    'core.middleware.AuditLogMiddleware',
    'core.middleware.KYCEnforcementMiddleware',
]

ROOT_URLCONF = 'blackrock.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates', BASE_DIR / 'blackrock' / 'templates', '/var/task/blackrock/templates'],
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
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
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


# Email settings (configure for production)
# ══════════════════════════════════════════════════════════════════════════
# EMAIL & OTP CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════
#
# ── QUICK SETUP GUIDE ────────────────────────────────────────────────────
#
# OPTION A — Gmail (simplest for testing)
#   1. Enable 2FA on your Google account
#   2. Generate an "App Password": myaccount.google.com → Security → App Passwords
#   3. Set EMAIL_HOST_USER = 'youraddress@gmail.com'
#   4. Set EMAIL_HOST_PASSWORD = 'your-16-char-app-password'
#
# OPTION B — SendGrid (recommended for production)
#   1. Sign up at sendgrid.com, create an API key
#   2. Set EMAIL_HOST = 'smtp.sendgrid.net'
#   3. Set EMAIL_HOST_USER = 'apikey'
#   4. Set EMAIL_HOST_PASSWORD = '<your-sendgrid-api-key>'
#
# OPTION C — Mailgun
#   EMAIL_HOST = 'smtp.mailgun.org'
#   EMAIL_HOST_USER = 'postmaster@yourdomain.mailgun.org'
#   EMAIL_HOST_PASSWORD = '<mailgun-smtp-password>'
#
# OPTION D — Console (development only — OTP appears in terminal)
#   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#   OTP_DEBUG_PRINT = True   ← always prints OTP to terminal
#
# ─────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────
# EMAIL CONFIGURATION (GMAIL SMTP - OPTION A)
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# EMAIL CONFIGURATION (GMAIL SMTP FIXED)
# ─────────────────────────────────────────────

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587

EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

EMAIL_HOST_USER = 'supportblackrock@gmail.com'
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default='')

EMAIL_TIMEOUT = 30
EMAIL_FAIL_SILENTLY = False

DEFAULT_FROM_EMAIL = 'BlackRock Support <supportblackrock@gmail.com>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# ── DEBUG (IMPORTANT FOR EMAIL TESTING) ──
DEBUG = True

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
