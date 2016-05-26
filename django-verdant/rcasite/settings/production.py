import socket
import raven

from .base import *

DEBUG = False

ALLOWED_HOSTS = ['rca-staging.torchboxapps.com', 'verdant-rca-staging.torchboxapps.com', 'verdant-rca-production.torchboxapps.com', 'www.rca.ac.uk', 'screens.rca.ac.uk']

TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)

BROKER_URL = 'redis://rca1.dh.bytemark.co.uk'
CACHES['default']['LOCATION'] = 'rca1.dh.bytemark.co.uk:6379:1'

WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.wagtailsearch.backends.elasticsearch.ElasticSearch',
        'INDEX': 'rca',
        'URLS': ['http://rca1.dh.bytemark.co.uk:8938/es1.3'],
        'ATOMIC_REBUILD': True,
    },
}

EMAIL_SUBJECT_PREFIX = '[rca-production - %s] ' % socket.gethostname().split('.')[0]
DEFAULT_FROM_EMAIL = 'publications@rca.ac.uk'
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = DEFAULT_FROM_EMAIL
EMAIL_HOST_PASSWORD = ''

# SERVER_EMAIL = "root@%s.dh.bytemark.co.uk" % socket.gethostname().split('.')[0]
SERVER_EMAIL = DEFAULT_FROM_EMAIL

MEDIA_ROOT = "/verdant-shared/media/"
STATIC_ROOT = "/verdant-shared/static/"

# BASE_URL required for notification emails
BASE_URL = 'http://www.rca.ac.uk'

# LDAP
from rca_ldap.settings import *

AUTH_LDAP_BIND_DN = ''
AUTH_LDAP_BIND_PASSWORD = ''
AUTH_LDAP_SERVER_URI = 'ldaps://194.80.196.3:636'

AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)

GOOGLE_ANALYTICS_ACCOUNT = 'UA-3809199-5'

try:
	from .local import *
except ImportError:
	pass


# Raven (sentry error logging)

# This must be after the .local import as RAVEN_DSN is set in local.py
if 'RAVEN_DSN' in os.environ:
    RAVEN_CONFIG = {
        'dsn': os.environ['RAVEN_DSN'],
        'release': raven.fetch_git_sha(os.path.dirname(os.path.abspath(PROJECT_ROOT))),
    }
