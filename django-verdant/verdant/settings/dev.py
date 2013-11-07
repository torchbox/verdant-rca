from .base import *

DEBUG = True
INSTALLED_APPS = list(INSTALLED_APPS) + ['devserver']

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

try:
    from .local import *
except ImportError:
    pass
