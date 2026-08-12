"""
Django settings — développement local.
Étend base.py avec debug toolbar et email console.
"""

from .base import *  # noqa: F401, F403

# --- Debug toolbar ---
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa: F405
INTERNAL_IPS = ["127.0.0.1"]

# --- Email console ---
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
