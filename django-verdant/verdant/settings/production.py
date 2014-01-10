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
VERDANTSEARCH_ES_URLS = ['http://rca1.dh.bytemark.co.uk:9200']

# BASE_URL required for notification emails
BASE_URL = 'http://www.rca.ac.uk'


try:
	from .local import *
except ImportError:
	pass
