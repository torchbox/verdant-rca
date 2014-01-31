from .base import *


DEBUG = False

ALLOWED_HOSTS = ['']

TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)

MEDIA_ROOT = "/verdant-shared/media/"
STATIC_ROOT = "/verdant-shared/static/"


try:
	from .local import *
except ImportError:
	pass
