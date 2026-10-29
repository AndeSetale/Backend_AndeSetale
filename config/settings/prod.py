from .base import *

DEBUG = False

# En prod, ALLOWED_HOSTS doit être défini dans le .env
# ex: ALLOWED_HOSTS=api.andesetale.sn,www.andesetale.sn

# Sécurité HTTPS
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000          # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

# Email SMTP (variables dans .env) — Django 5.2+ : utilise MAILERS
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "HOST": env("EMAIL_HOST", default="smtp.gmail.com"),
        "PORT": env.int("EMAIL_PORT", default=587),
        "USE_TLS": True,
        "USERNAME": env("EMAIL_HOST_USER", default=""),
        "PASSWORD": env("EMAIL_HOST_PASSWORD", default=""),
        "DEFAULT_FROM_EMAIL": env("DEFAULT_FROM_EMAIL", default="noreply@andesetale.sn"),
    }
}
