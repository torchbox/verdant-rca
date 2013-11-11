from .base import *

DEBUG = False

ALLOWED_HOSTS = ['rca-staging.torchboxapps.com', 'verdant-rca-staging.torchboxapps.com', 'verdant-rca-production.torchboxapps.com', 'www.rca.ac.uk']

try:
	from .local import *
except ImportError:
	pass
