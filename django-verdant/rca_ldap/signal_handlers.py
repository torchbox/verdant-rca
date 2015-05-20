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
                for group_name in role['groups']:
                    try:
                        group_obj = Group.objects.get(name=group_name)
                        user.groups.add(group_obj)
                    except Group.DoesNotExist:
                        continue

    # additionally, check the student status (for profile editing)
    # according to documentation in codebase, student group is determined by the "Job title" in active directory,
    # which itself maps to 'title' in LDAP.
    if 'title' in ldap_user._user_attrs:
        title = ' '.join(ldap_user._user_attrs['title']).lower()

        # for reference see the specification on ticket #645:
        if title.startswith('ma student') or '/ ma student' in title:
            user.groups.add(Group.objects.get(name='MA Students'))
        elif title.startswith('mphil student') or '/ mphil student' in title:
            user.groups.add(Group.objects.get(name='MPhil Students'))
        elif title.startswith('phd student') or '/ phd student' in title:
            user.groups.add(Group.objects.get(name='PhD Students'))


def register_signal_handlers():
    populate_user.connect(populate_user_signal_handler)