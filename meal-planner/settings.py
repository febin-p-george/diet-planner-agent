import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# FIX: Use environment variables, never hardcode secrets.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "change-me-in-production-please")
DEBUG = os.environ.get("DEBUG", "False") == "True"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".vercel.app",      # covers all *.vercel.app domains
    ".railway.app",     # if you use Railway instead
    ".onrender.com",    # if you use Render instead
]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "chat",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serves static files on Vercel
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "meal_planner.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.request",
        ],
    },
}]

WSGI_APPLICATION = "meal_planner.wsgi.application"

# No database needed (ADK uses InMemorySessionService)
DATABASES = {}

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"