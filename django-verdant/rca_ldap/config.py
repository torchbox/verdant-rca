from django_auth_ldap.config import LDAPSearch


class LDAPSearchRCA(LDAPSearch):
    """
    An extension of the django-auth-ldap.LDAPSearch class to allow user roles to be easily configured
    """

    def __init__(self, *args, **kwargs):
        if 'role' in kwargs:
            self.role = kwargs['role']
            del kwargs['role']
        else:
            self.role = None

        return super(LDAPSearchRCA, self).__init__(*args, **kwargs)

    def _process_results(self, *args, **kwargs):
        results = super(LDAPSearchRCA, self)._process_results(*args, **kwargs)

        # Sneak role into results
        for result in results:
            result[1]['role'] = self.role

        return results