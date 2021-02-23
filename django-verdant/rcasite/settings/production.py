import os

from .base import *  # noqa

# Do not set SECRET_KEY, Postgres or LDAP password or any other sensitive data here.
# Instead, use environment variables or create a local.py file on the server.

# Disable debug mode
DEBUG = False


# Use cached template loader
TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)

# Google Analytics
GOOGLE_ANALYTICS_ACCOUNT = 'UA-3809199-5'

SILVERPOP_ID = 'd871c05-15671ce6a9e-c6f842ded9e6d11c5ffebd715e129037'
SILVERPOP_BRANDEDDOMAINS = 'www.pages05.net,rcawebsite,studentenquiry97.mkt4116.com'


# Compress static files offline and minify CSS
# http://django-compressor.readthedocs.org/en/latest/settings/#django.conf.settings.COMPRESS_OFFLINE
COMPRESS_OFFLINE = True
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter',
]
COMPRESS_CSS_HASHING_METHOD = 'content'

# Cache everything for 30 minutes
# This only applies to pages that do not have a more specific cache-control
# setting. See urls.py
CACHE_CONTROL_S_MAXAGE = 30 * 60


# Configuration from environment variables
# Alternatively, you can set these in a local.py file on the server
env = os.environ.copy()

# LDAP authentication
from rca_ldap.settings import *

if 'AUTH_LDAP_BIND_DN' in env:
    AUTH_LDAP_BIND_DN = env['AUTH_LDAP_BIND_DN']
if 'AUTH_LDAP_BIND_PASSWORD' in env:
    AUTH_LDAP_BIND_PASSWORD = env['AUTH_LDAP_BIND_PASSWORD']
if 'AUTH_LDAP_SERVER_URI' in env:
    AUTH_LDAP_SERVER_URI = env['AUTH_LDAP_SERVER_URI']

AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# On Torchbox servers, many environment variables are prefixed with "CFG_"
for key, value in os.environ.items():
    if key.startswith('CFG_'):
        env[key[4:]] = value

# Basic configuration
APP_NAME = env.get('APP_NAME', 'rca')

if 'SECRET_KEY' in env:
    SECRET_KEY = env['SECRET_KEY']

if 'ALLOWED_HOSTS' in env:
    ALLOWED_HOSTS = env['ALLOWED_HOSTS'].split(',')

if 'PRIMARY_HOST' in env:
    BASE_URL = 'http://%s' % env['PRIMARY_HOST']

if 'CACHE_PURGE_URL' in env:
    INSTALLED_APPS += ('wagtail.contrib.wagtailfrontendcache', )  # noqa
    WAGTAILFRONTENDCACHE = {
        'default': {
            'BACKEND': 'wagtail.contrib.wagtailfrontendcache.backends.HTTPBackend',
            'LOCATION': env['CACHE_PURGE_URL'],
        },
    }

if 'STATIC_URL' in env:
    STATIC_URL = env['STATIC_URL']

if 'STATIC_DIR' in env:
    STATIC_ROOT = env['STATIC_DIR']

if 'MEDIA_URL' in env:
    MEDIA_URL = env['MEDIA_URL']

if 'MEDIA_DIR' in env:
    MEDIA_ROOT = env['MEDIA_DIR']


# Email settings
# We use SMTP to send emails. We typically use transactional email services
# that let us use SMTP.
# https://docs.djangoproject.com/en/2.1/topics/email/

# https://docs.djangoproject.com/en/stable/ref/settings/#email-host
if "EMAIL_HOST" in env:
    EMAIL_HOST = env["EMAIL_HOST"]

# https://docs.djangoproject.com/en/stable/ref/settings/#email-port
if "EMAIL_PORT" in env:
    try:
        EMAIL_PORT = int(env["EMAIL_PORT"])
    except ValueError:
        pass

# https://docs.djangoproject.com/en/stable/ref/settings/#email-host-user
if "EMAIL_HOST_USER" in env:
    EMAIL_HOST_USER = env["EMAIL_HOST_USER"]

# https://docs.djangoproject.com/en/stable/ref/settings/#email-host-password
if "EMAIL_HOST_PASSWORD" in env:
    EMAIL_HOST_PASSWORD = env["EMAIL_HOST_PASSWORD"]

# https://docs.djangoproject.com/en/stable/ref/settings/#email-use-tls
if env.get("EMAIL_USE_TLS", "false").lower().strip() == "true":
    EMAIL_USE_TLS = True

# https://docs.djangoproject.com/en/stable/ref/settings/#email-use-ssl
if env.get("EMAIL_USE_SSL", "false").lower().strip() == "true":
    EMAIL_USE_SSL = True

# https://docs.djangoproject.com/en/stable/ref/settings/#email-subject-prefix
if "EMAIL_SUBJECT_PREFIX" in env:
    EMAIL_SUBJECT_PREFIX = env["EMAIL_SUBJECT_PREFIX"]

# SERVER_EMAIL is used to send emails to administrators.
# https://docs.djangoproject.com/en/stable/ref/settings/#server-email
# DEFAULT_FROM_EMAIL is used as a default for any mail send from the website to
# the users.
# https://docs.djangoproject.com/en/stable/ref/settings/#default-from-email
if "SERVER_EMAIL" in env:
    SERVER_EMAIL = DEFAULT_FROM_EMAIL = env["SERVER_EMAIL"]


# Redis
# Redis location can either be passed through with REDIS_HOST or REDIS_SOCKET

if 'REDIS_URL' in env:
    REDIS_LOCATION = env['REDIS_URL']
    BROKER_URL = env['REDIS_URL']

elif 'REDIS_HOST' in env:
    REDIS_LOCATION = env['REDIS_HOST']
    BROKER_URL = 'redis://%s' % env['REDIS_HOST']

elif 'REDIS_SOCKET' in env:
    REDIS_LOCATION = 'unix://%s' % env['REDIS_SOCKET']
    BROKER_URL = 'redis+socket://%s' % env['REDIS_SOCKET']

else:
    REDIS_LOCATION = None


if REDIS_LOCATION is not None:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_LOCATION,
            'KEY_PREFIX': APP_NAME,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }


# Elasticsearch
ELASTICSEARCH_URL = None

if 'ELASTICSEARCH_URL' in env:
    ELASTICSEARCH_URL = env['ELASTICSEARCH_URL']

elif 'SEARCHBOX_URL' in env:
    ELASTICSEARCH_URL = env['SEARCHBOX_URL']

if ELASTICSEARCH_URL is not None:
    WAGTAILSEARCH_BACKENDS = {
        'default': {
            'BACKEND': 'wagtail.wagtailsearch.backends.elasticsearch',
            'URLS': [ELASTICSEARCH_URL],
            'INDEX': APP_NAME,
            'TIMEOUT': 30,
            'OPTIONS': {},
        },
    }

if 'TWITTER_CONSUMER_KEY' in env:
    TWITTER_CONSUMER_KEY = env['TWITTER_CONSUMER_KEY']
if 'TWITTER_CONSUMER_SECRET' in env:
    TWITTER_CONSUMER_SECRET = env['TWITTER_CONSUMER_SECRET']
if 'TWITTER_ACCESS_TOKEN' in env:
    TWITTER_ACCESS_TOKEN = env['TWITTER_ACCESS_TOKEN']
if 'TWITTER_ACCESS_TOKEN_SECRET' in env:
    TWITTER_ACCESS_TOKEN_SECRET = env['TWITTER_ACCESS_TOKEN_SECRET']

try:
    from .local import *  # noqa
except ImportError:
    pass

