import socket

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
    },
}

EMAIL_SUBJECT_PREFIX = "[rca-production] "
DEFAULT_FROM_EMAIL = 'publications@rca.ac.uk'
SERVER_EMAIL = "root@%s.dh.bytemark.co.uk" % socket.gethostname().split('.')[0]

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
