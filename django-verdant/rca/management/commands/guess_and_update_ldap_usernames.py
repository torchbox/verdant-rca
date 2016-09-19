from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings

from wagtail.wagtailcore.models import Site

from rca.models import RcaImage, StaffPage


import ldap
from django_auth_ldap.config import LDAPSearch, LDAPSearchUnion


STAFF_DN    = 'OU=Staff,DC=rca,DC=ac,DC=uk'
STUDENTS_DN = 'OU=Students,DC=rca,DC=ac,DC=uk'


class MultipleUsersReturned(Exception):
    pass


class LDAPConnection(object):
    def __init__(self, dn=settings.AUTH_LDAP_BIND_DN, password=settings.AUTH_LDAP_BIND_PASSWORD):
        self.dn = dn
        self.password = password

    def __enter__(self):
        self.conn = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
        for k, v in settings.AUTH_LDAP_CONNECTION_OPTIONS.items():
            self.conn.set_option(k, v)
        self.conn.simple_bind_s(self.dn, self.password)
        return self.conn

    def __exit__(self, type, value, traceback):
        try:
            self.conn.unbind_s()
        except Exception:
            pass


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--commit',
            action='store_true',
            dest='commit',
            default=False,
        ),
    )

    def handle(self, commit, **options):
        updated = []
        not_updated = []
        with LDAPConnection() as conn:
            ad_usernames = LDAPSearch(STAFF_DN, ldap.SCOPE_SUBTREE, "(sAMAccountName=*)").execute(conn)

        ad_usernames = [d[1].get('sAMAccountName')[0] for d in ad_usernames if d[1].get('sAMAccountName')]

        for staff_page in StaffPage.objects.filter(ad_username=''):
            ad_username_guess = ('%s.%s' % (staff_page.first_name, staff_page.last_name)).lower()
            if ad_username_guess in ad_usernames:
                staff_page.ad_username = ad_username_guess
                if commit:
                    staff_page.save()
                updated.append(staff_page.id)
            else:
                not_updated.append(staff_page.id)

        root_url = Site.objects.get(is_default_site=True).root_url
        for id in updated:
            print 'Updated: %s/admin/pages/%d/edit/' % (root_url, id)

        for id in not_updated:
            print 'Not updated: %s/admin/pages/%d/edit/' % (root_url, id)

        if not commit:
            print "The --commit option wasn't used, so no changes were made to the database."
