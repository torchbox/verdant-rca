# Django settings for RCA Wagtail project.

import os
import sys
import raven
import dj_database_url
from raven.exceptions import InvalidGitRepository

env = os.environ.copy()

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
BASE_DIR = os.path.dirname(PROJECT_ROOT)

# Modify sys.path to include the lib directory
sys.path.append(os.path.join(PROJECT_ROOT, "lib"))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Verdant RCA errors', 'verdant-rca-errors@torchbox.com'),
)

MANAGERS = ADMINS

# Database
if 'DATABASE_URL' in env:
    DATABASES = {'default': dj_database_url.config()}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-gb'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
# MW 2013-09-24: L10n needs to be disabled in order to recognise formats like
# "24 Sep 2013" in FriendlyDateField, because Python's strptime doesn't support
# localised month names. https://code.djangoproject.com/ticket/13339
USE_L10N = False

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
    'compressor.finders.CompressorFinder',
)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Make this unique, and don't share it with anybody.
SECRET_KEY = 'ncbi!(%ae=!*2ififuzlfq@=5*opoakdn5g%m9g^++c6@jm^r)'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'wagtail.wagtailcore.middleware.SiteMiddleware',
    'wagtail.wagtailredirects.middleware.RedirectMiddleware',
]

from django.conf import global_settings
TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + [
    'django.core.context_processors.request',
    'rca.context_processors.global_vars',
]

ROOT_URLCONF = 'rcasite.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'rcasite.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = [
    'scout_apm.django', # should be listed first

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    # 'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'compressor',
    'template_timings_panel',
    'taggit',
    'twitter',  # the app used to proxy the Twitter REST API
    'widget_tweaks',
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',

    # Must be above wagtail
    'wagtailadmin_overridden_templates',

    'wagtail.wagtailcore',
    'wagtail.wagtailadmin',
    'wagtail.wagtaildocs',
    'wagtail.wagtailsnippets',
    'wagtail.wagtailusers',
    'wagtail.wagtailsites',
    'wagtail.wagtailimages',
    'wagtail.wagtailembeds',
    'wagtail.wagtailsearch',
    'wagtail.wagtailredirects',
    'wagtail.contrib.wagtailsearchpromotions',
    'wagtail.contrib.settings',
    'wagtail.wagtailforms',
    'wagtail.contrib.modeladmin',
    'django.contrib.sitemaps',
    'rcasitemaps',

    'wagtailcaptcha',
    'captcha',
    'corsheaders',

    'webhooks',
    'taxonomy',
    'donations',

    'rca',
    'rca.standard_stream_page',
    'rca.utils',

    'rca_signage',
    'rca_ldap',
    'rca_show',
    'rca_ee',           # executive education
    'student_profiles',
    'shortcourses',
]

EMAIL_SUBJECT_PREFIX = '[wagtail] '

INTERNAL_IPS = ('127.0.0.1', '10.0.2.2')

# django-debug-toolbar settings
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    'debug_toolbar.panels.logger.LoggingPanel',
    'template_timings_panel.panels.TemplateTimings.TemplateTimings',
)

# django-compressor settings
COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'django_libsass.SassCompiler'),
    ('text/coffeescript', 'coffee --compile --stdio'),
    ('text/less', 'lessc {infile} {outfile}'),
)
COMPRESS_OFFLINE = True
COMPRESS_OFFLINE_CONTEXT = 'rcasite.utils.offline_context'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        # Send logs with at least INFO level to the console.
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        # Send logs with level of at least ERROR to Sentry.
        "sentry": {
            "level": "ERROR",
            "class": "raven.contrib.django.raven_compat.handlers.SentryHandler",
        },
    },
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s][%(process)d][%(levelname)s][%(name)s] %(message)s"
        }
    },
    "loggers": {
        "verdant-rca": {
            "handlers": ["console", "sentry"],
            "level": "DEBUG",
            "propagate": False,
        },
        "wagtail": {
            "handlers": ["console", "sentry"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "sentry"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console", "sentry"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}


# Raven (Sentry) configuration.
# See instructions on the intranet:
# https://intranet.torchbox.com/delivering-projects/tech/starting-new-project/#sentry
if "SENTRY_DSN" in env:
    INSTALLED_APPS.append("raven.contrib.django.raven_compat")

    RAVEN_CONFIG = {"dsn": env["SENTRY_DSN"], "tags": {}}

    # Specifying the programming language as a tag can be useful when
    # e.g. JavaScript error logging is enabled within the same project,
    # so that errors can be filtered by the programming language too.
    # The 'lang' tag is just an arbitrarily chosen one; any other tags can be used as well.
    # It has to be overridden in JavaScript: Raven.setTagsContext({lang: 'javascript'});
    RAVEN_CONFIG["tags"]["lang"] = "python"

    # Prevent logging errors from the django shell.
    # Errors from other management commands will be still logged.
    if len(sys.argv) > 1 and sys.argv[1] in ["shell", "shell_plus"]:
        RAVEN_CONFIG["ignore_exceptions"] = ["*"]

    # There's a chooser to toggle between environments at the top right corner on sentry.io
    # Values are typically 'staging' or 'production' but can be set to anything else if needed.
    # dokku config:set verdant-rca SENTRY_ENVIRONMENT=staging
    # heroku config:set SENTRY_ENVIRONMENT=production
    if "SENTRY_ENVIRONMENT" in env:
        RAVEN_CONFIG["environment"] = env["SENTRY_ENVIRONMENT"]

    # We first assume that the Git repository is present and we can detect the
    # commit hash from it.
    try:
        RAVEN_CONFIG["release"] = raven.fetch_git_sha(BASE_DIR)
    except InvalidGitRepository:
        try:
            # But if it's not, we assume that the commit hash is available in
            # the GIT_REV environment variable. It's a default environment
            # variable used on Dokku:
            # http://dokku.viewdocs.io/dokku/deployment/methods/git/#configuring-the-git_rev-environment-variable
            RAVEN_CONFIG["release"] = env["GIT_REV"]
        except KeyError:
            try:
                # Assume this is a Heroku-hosted app with the "runtime-dyno-metadata" lab enabled
                RAVEN_CONFIG["release"] = env["HEROKU_RELEASE_VERSION"]
            except KeyError:
                # If there's no commit hash, we do not set a specific release.
                pass



CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': '127.0.0.1:6379:1',
        'KEY_PREFIX': 'rca',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# WAGTAIL SETTINGS

WAGTAIL_SITE_NAME = 'RCA'

# Override the Image class used by wagtailimages with a custom one
WAGTAILIMAGES_IMAGE_MODEL = 'rca.RcaImage'

WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.wagtailsearch.backends.elasticsearch.ElasticSearch',
        'INDEX': 'verdant',
    },
}

# Hide password management / recovery options, as RCA uses LDAP instead
WAGTAIL_PASSWORD_MANAGEMENT_ENABLED = False

BROKER_URL = 'redis://'

PASSWORD_REQUIRED_TEMPLATE = "rca/login.html"

GOOGLE_ANALYTICS_ACCOUNT = ''

SILVERPOP_ID = ''
SILVERPOP_BRANDEDDOMAINS = ''

# ReCaptcha settings
if 'RECAPTCHA_PUBLIC_KEY' in env:
    RECAPTCHA_PUBLIC_KEY = env['RECAPTCHA_PUBLIC_KEY']
if 'RECAPTCHA_PRIVATE_KEY' in env:
    RECAPTCHA_PRIVATE_KEY = env['RECAPTCHA_PRIVATE_KEY']

NOCAPTCHA = True
RECAPTCHA_USE_SSL = True

# CORS settings
if 'CORS_ORIGIN_WHITELIST' in env:
    CORS_ORIGIN_WHITELIST = env['CORS_ORIGIN_WHITELIST'].split(',')


CORS_URLS_REGEX = r'^/api/.*$'
CORS_ALLOW_METHODS = ['GET', 'OPTIONS']


if 'AWS_STORAGE_BUCKET_NAME' in env:

    # Add django-storages to the installed apps
    INSTALLED_APPS.append('storages')

    # https://docs.djangoproject.com/en/stable/ref/settings/#default-file-storage
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

    AWS_STORAGE_BUCKET_NAME = env['AWS_STORAGE_BUCKET_NAME']

    # Disables signing of the S3 objects' URLs. When set to True it
    # will append authorization querystring to each URL.
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_HOST = env.get('AWS_S3_HOST')

    # Do not allow overriding files on S3 as per Wagtail docs recommendation:
    # https://docs.wagtail.io/en/stable/advanced_topics/deploying.html#cloud-storage
    # Not having this setting may have consequences in losing files.
    AWS_S3_FILE_OVERWRITE = False

    # We generally use this setting in the production to put the S3 bucket
    # behind a CDN using a custom domain, e.g. media.llamasavers.com.
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#cloudfront
    if 'AWS_S3_CUSTOM_DOMAIN' in env:
        AWS_S3_CUSTOM_DOMAIN = env['AWS_S3_CUSTOM_DOMAIN']

    # This settings lets you force using http or https protocol when generating
    # the URLs to the files. Set https as default.
    # https://github.com/jschneier/django-storages/blob/10d1929de5e0318dbd63d715db4bebc9a42257b5/storages/backends/s3boto3.py#L217
    AWS_S3_URL_PROTOCOL = env.get('AWS_S3_URL_PROTOCOL', 'https:')

    # Set S3 calling format
    # See https://torchbox.slack.com/archives/C03QAAC93/p1575976449104900
    from boto.s3.connection import OrdinaryCallingFormat
    AWS_S3_CALLING_FORMAT = OrdinaryCallingFormat()

if 'FRONTEND_CACHE_CLOUDFLARE_TOKEN' in env:
    INSTALLED_APPS.append('wagtail.contrib.frontend_cache')
    WAGTAILFRONTENDCACHE = {
        'default': {
            'BACKEND': 'wagtail.contrib.frontend_cache.backends.CloudflareBackend',
            'EMAIL': env['FRONTEND_CACHE_CLOUDFLARE_EMAIL'],
            'TOKEN': env['FRONTEND_CACHE_CLOUDFLARE_TOKEN'],
            'ZONEID': env['FRONTEND_CACHE_CLOUDFLARE_ZONEID'],
        },
    }

# Force HTTPS redirect
# https://docs.djangoproject.com/en/stable/ref/settings/#secure-ssl-redirect
if env.get('SECURE_SSL_REDIRECT', 'true').strip().lower() == 'true':
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Basic authentication settings
# Using django-basicauth here as django-basic-auth-ip-whitelist doesn't have
# python 2.7 compatibility
if env.get("BASIC_AUTH_ENABLED", "false").lower().strip() == "true":
    # Insert basic auth as a first middleware to be checked first, before
    # anything else.
    MIDDLEWARE_CLASSES.insert(0, "basicauth.middleware.BasicAuthMiddleware")

    # This is the credentials users will have to use to access the site.
    BASIC_AUTH_LOGIN = env.get("BASIC_AUTH_LOGIN", "rca")
    BASIC_AUTH_PASSWORD = env.get("BASIC_AUTH_PASSWORD", "showmerca")
    BASICAUTH_USERS = {}
    BASICAUTH_USERS[BASIC_AUTH_LOGIN] = BASIC_AUTH_PASSWORD

SEO_NOINDEX = env.get('SEO_NOINDEX', 'false').lower() == 'true'

# Email settings
# We use SMTP to send emails. We typically use transactional email services
# that let us use SMTP.
# https://docs.djangoproject.com/en/2.1/topics/email/

# https://docs.djangoproject.com/en/stable/ref/settings/#email-host
if 'EMAIL_HOST' in env:
    EMAIL_HOST = env['EMAIL_HOST']

# https://docs.djangoproject.com/en/stable/ref/settings/#email-port
if 'EMAIL_PORT' in env:
    try:
        EMAIL_PORT = int(env['EMAIL_PORT'])
    except ValueError:
        pass

# https://docs.djangoproject.com/en/stable/ref/settings/#email-host-user
if 'EMAIL_HOST_USER' in env:
    EMAIL_HOST_USER = env['EMAIL_HOST_USER']

# https://docs.djangoproject.com/en/stable/ref/settings/#email-host-password
if 'EMAIL_HOST_PASSWORD' in env:
    EMAIL_HOST_PASSWORD = env['EMAIL_HOST_PASSWORD']

# https://docs.djangoproject.com/en/stable/ref/settings/#email-use-tls
if env.get('EMAIL_USE_TLS', 'false').lower().strip() == 'true':
    EMAIL_USE_TLS = True

# https://docs.djangoproject.com/en/stable/ref/settings/#email-use-ssl
if env.get('EMAIL_USE_SSL', 'false').lower().strip() == 'true':
    EMAIL_USE_SSL = True

# https://docs.djangoproject.com/en/stable/ref/settings/#email-subject-prefix
if 'EMAIL_SUBJECT_PREFIX' in env:
    EMAIL_SUBJECT_PREFIX = env['EMAIL_SUBJECT_PREFIX']

# SERVER_EMAIL is used to send emails to administrators.
# https://docs.djangoproject.com/en/stable/ref/settings/#server-email
# DEFAULT_FROM_EMAIL is used as a default for any mail send from the website to
# the users.
# https://docs.djangoproject.com/en/stable/ref/settings/#default-from-email
if 'SERVER_EMAIL' in env:
    SERVER_EMAIL = DEFAULT_FROM_EMAIL = env['SERVER_EMAIL']

if 'EMAIL_SENDER' in env:
    DEFAULT_FROM_EMAIL = env['EMAIL_SENDER']

# URL (including token) to post a request for page
# to be imported/synced to the intranet. Example:
# https://intranet.rca.ac.uk/sync/trigger_import/{id}/?token=tokenfromintranetconfig
if 'INTRANET_PUSH_URL' in env:
    INTRANET_PUSH_URL = env['INTRANET_PUSH_URL']

if 'ACCESS_PLANIT_COMPANY_ID' in env:
    ACCESS_PLANIT_COMPANY_ID = env['ACCESS_PLANIT_COMPANY_ID']

if 'EMBEDLY_KEY' in env:
    EMBEDLY_KEY = env['EMBEDLY_KEY']
if 'STRIPE_SECRET_KEY' in env:
    STRIPE_SECRET_KEY = env['STRIPE_SECRET_KEY']
if 'STRIPE_PUBLISHABLE_KEY' in env:
    STRIPE_PUBLISHABLE_KEY = env['STRIPE_PUBLISHABLE_KEY']
if 'WEBHOOKS_PAGE_PUBLISHED' in env:
    WEBHOOKS_PAGE_PUBLISHED = [env['WEBHOOKS_PAGE_PUBLISHED'],]
if 'WEBHOOKS_PAGE_UNPUBLISHED' in env:
    WEBHOOKS_PAGE_UNPUBLISHED = [env['WEBHOOKS_PAGE_UNPUBLISHED'],]

CSRF_TRUSTED_ORIGINS = [
    'www.rca.ac.uk'
]

RCA_LOGIN_DISABLED = False

if "PRIMARY_HOST" in env:
    BASE_URL = "https://{}".format(env["PRIMARY_HOST"])
