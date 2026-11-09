"""Production settings for WorkNeuron on a WSGI host such as PythonAnywhere."""

from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F401,F403


def _required(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise ImproperlyConfigured(f"{name} must be set in production.")
    return value


DEBUG = False
SECRET_KEY = _required("DJANGO_SECRET_KEY")
STATIC_URL = "/static/"
MEDIA_URL = os.getenv("MEDIA_URL", "/media/")
ALLOWED_HOSTS = [host.strip() for host in _required("DJANGO_ALLOWED_HOSTS").split(",") if host.strip()]
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in _required("CORS_ALLOWED_ORIGINS").split(",") if origin.strip()]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in _required("CSRF_TRUSTED_ORIGINS").split(",") if origin.strip()]

# PythonAnywhere supplies HTTPS at its edge and forwards the original scheme.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = max(1, int(os.getenv("SECURE_HSTS_SECONDS", "31536000")))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "True").lower() in {"1", "true", "yes"}

# A production database must be explicit.  PythonAnywhere-hosted PostgreSQL
# values are entered as DB_* variables; DATABASE_URL also remains supported.
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)}
else:
    DATABASES = {
        "default": {
            "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
            "NAME": _required("DB_NAME"),
            "USER": _required("DB_USER"),
            "PASSWORD": _required("DB_PASSWORD"),
            "HOST": _required("DB_HOST"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }

# Local disk is acceptable for a single-instance proof of concept only.  The
# guide explains the backup and private-document implications.
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", str(BASE_DIR / "media")))
if not MEDIA_ROOT.is_absolute():
    MEDIA_ROOT = BASE_DIR / MEDIA_ROOT

