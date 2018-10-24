from .base import *

DEBUG = True
INSTALLED_APPS = list(INSTALLED_APPS) + ['wagtail.contrib.wagtailstyleguide']

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# BASE_URL required for notification emails
BASE_URL = 'http://localhost:8111'

# INSTALLED_APPS += (
#     'debug_toolbar',
# )

# MIDDLEWARE_CLASSES += (
#     'debug_toolbar.middleware.DebugToolbarMiddleware',
# )

try:
    from .local import *
except ImportError:
    pass
