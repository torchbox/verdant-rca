from .base import *

DEBUG = False

ALLOWED_HOSTS = ['rca-staging.torchboxapps.com', 'verdant-rca-staging.torchboxapps.com', 'verdant-rca-production.torchboxapps.com', 'www.rca.ac.uk']

TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)



# LDAP
import ldap
from django_auth_ldap.config import LDAPSearchUnion
from rca_ldap.config import LDAPSearchRCA

# Basic config
AUTH_LDAP_BIND_DN = ''
AUTH_LDAP_BIND_PASSWORD = ''
AUTH_LDAP_SERVER_URI = 'ldaps://194.80.196.3:636'

# Filter strings
def get_filter_string(base, **kwargs):
    filter_string = base

    for field, value in kwargs.items():
        filter_string = ''.join([
            '(&',
                filter_string,
                '(', field, '=', value, ')',
            ')'
        ])

    return filter_string

FILTER_BASE = '(uid=%(user)s)'
FILTER_SUPER_PUBLISHERS = get_filter_string(FILTER_BASE, memberOf='CN=CMS Super-Publishers,OU=Media Relations & Marketing,OU=Administration,OU=Staff,DC=rca,DC=ac,DC=uk')
FILTER_PUBLISHERS = get_filter_string(FILTER_BASE, memberOf='CN=CMS Publishers,OU=Media Relations & Marketing,OU=Administration,OU=Staff,DC=rca,DC=ac,DC=uk')
FILTER_CONTRIBUTERS = get_filter_string(FILTER_BASE, memberOf='CN=CMS Contributors,OU=Media Relations & Marketing,OU=Administration,OU=Staff,DC=rca,DC=ac,DC=uk')
FILTER_VISITORS = get_filter_string(FILTER_BASE, memberOf='CN=CMS Visitors,OU=Media Relations & Marketing,OU=Administration,OU=Staff,DC=rca,DC=ac,DC=uk')

# Roles
ROLE_ADMIN  = dict(superuser=True, groups=[])
ROLE_MOD    = dict(superuser=False, groups=['Moderators'])
ROLE_EDITOR = dict(superuser=False, groups=['Editors'])
ROLE_USER   = dict(superuser=False, groups=[])

# Distinguished names
STAFF_DN    = 'OU=Staff,DC=rca,DC=ac,DC=uk'
STUDENTS_DN = 'OU=Students,DC=rca,DC=ac,DC=uk'

# Search
AUTH_LDAP_USER_SEARCH = LDAPSearchUnion(
    # Staff
    LDAPSearchRCA(STAFF_DN, ldap.SCOPE_SUBTREE, FILTER_SUPER_PUBLISHERS, role=ROLE_ADMIN),
    LDAPSearchRCA(STAFF_DN, ldap.SCOPE_SUBTREE, FILTER_PUBLISHERS, role=ROLE_MOD),
    LDAPSearchRCA(STAFF_DN, ldap.SCOPE_SUBTREE, FILTER_CONTRIBUTERS, role=ROLE_EDITOR),
    LDAPSearchRCA(STAFF_DN, ldap.SCOPE_SUBTREE, FILTER_VISITORS, role=ROLE_USER),

    # Students
    LDAPSearchRCA(STUDENTS_DN, ldap.SCOPE_SUBTREE, FILTER_BASE, role=ROLE_USER),
)


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'django_auth_ldap.backend.LDAPBackend',
)



try:
	from .local import *
except ImportError:
	pass
