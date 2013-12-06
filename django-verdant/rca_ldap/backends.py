from django.contrib.auth.models import User
import ldap


class LDAPBackend(object):
    def authenticate(self, username=None, password=None):
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None