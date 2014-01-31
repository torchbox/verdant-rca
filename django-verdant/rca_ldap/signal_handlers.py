from django_auth_ldap.backend import populate_user
from django.contrib.auth.models import Group


def populate_user_signal_handler(user, ldap_user, **kwargs):
    # Make sure that this user is converted to an LDAP user
    user.set_unusable_password()

    # Check if role is set
    if 'role' in ldap_user._user_attrs:
        role = ldap_user._user_attrs['role']

        # Apply role to user
        if role is not None:
            # Superuser
            if 'superuser' in role:
                user.is_superuser = bool(role['superuser'])
                user.is_staff = user.is_superuser

            # Groups
            if 'groups' in role:
                # Get group list
                groups = []
                for group_name in role['groups']:
                    try:
                        group_obj = Group.objects.get(name=group_name)
                        groups.append(group_obj.pk)
                    except Group.DoesNotExist:
                        continue

                # Set groups
                user.groups = groups


def register_signal_handlers():
    populate_user.connect(populate_user_signal_handler)