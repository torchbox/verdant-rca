from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify

from wagtail.wagtailcore.models import Site

from rca.models import RcaImage, StaffPage, NewStudentPage


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
        make_option('--students',
            action='store_true',
            dest='students',
            default=False,
        ),
    )

    def guess_and_update_ldap_usernames(self, dn, model, commit=False):
        """
        Finds pages whose 'ad_username' field is blank attempts to guess the correct value
        based on the 'first_name' and 'last_name' fields.

        The guess is checked against LDAP. If a user with that username exists, the value is
        saved, otherwise the value is discarded leaving 'ad_username' blank.

        This returns two lists of page ids, the first list contains ids of the pages that a
        username was successfully guessed for. The second list contains the ids of the pages
        for which a guess was attempted but the guessed username didn't exist in LDAP.
        """
        updated = []
        not_updated = []

        with LDAPConnection() as conn:
            ad_usernames = LDAPSearch(dn, ldap.SCOPE_SUBTREE, "(sAMAccountName=*)").execute(conn)

        ad_usernames = [d[1].get('sAMAccountName')[0] for d in ad_usernames if d[1].get('sAMAccountName')]

        for page in model.objects.filter(ad_username=''):
            ad_username_guess = ('%s.%s' % (slugify(page.first_name), slugify(page.last_name)))
            if ad_username_guess in ad_usernames:
                page.ad_username = ad_username_guess
                if commit:
                    page.save()
                updated.append(page.id)
            else:
                not_updated.append(page.id)

        return updated, not_updated

    def handle(self, commit, students, **options):
        if students:
            updated, not_updated = self.guess_and_update_ldap_usernames(STUDENTS_DN, NewStudentPage, commit=commit)
        else:
            updated, not_updated = self.guess_and_update_ldap_usernames(STAFF_DN, StaffPage, commit=commit)

        root_url = Site.objects.get(is_default_site=True).root_url
        for id in updated:
            print 'Updated: %s/admin/pages/%d/edit/' % (root_url, id)

        for id in not_updated:
            print 'Not updated: %s/admin/pages/%d/edit/' % (root_url, id)

        if not commit:
            print "The --commit option wasn't used, so no changes were made to the database."
