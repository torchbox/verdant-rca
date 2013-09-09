from .base import *

DEBUG = True
COMPRESS_ENABLED = False
COMPRESS_REBUILD_TIMEOUT = 1000

INSTALLED_APPS = list(INSTALLED_APPS) + ['devserver']

try:
	from .local import *
except ImportError:
	pass
