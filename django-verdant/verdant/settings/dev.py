from .base import *

DEBUG = True
# INSTALLED_APPS = list(INSTALLED_APPS) + ['devserver']  # currently broken on Django 1.6 - see https://code.djangoproject.com/ticket/21348

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

try:
    from .local import *
except ImportError:
    pass
