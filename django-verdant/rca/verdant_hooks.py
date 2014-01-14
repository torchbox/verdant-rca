from verdantadmin import hooks
from verdantadmin.menu import MenuItem

from django.core.urlresolvers import reverse

def user_is_student(user):
    return [group.name for group in user.groups.all()] == ['Students']

def construct_main_menu(request, menu_items):
    if user_is_student(request.user):
        # remove Explorer and Search items from the menu.
        # assigning menu_items[:] will modify the list passed in
        menu_items[:] = [item for item in menu_items if item.name not in ('explorer', 'search')]

        # insert RCA Now item in place
        menu_items.append(
            MenuItem('RCA Now', reverse('rca_now_editor_index'), classnames='icon icon-doc-full-inverse', order=100)
        )

hooks.register('construct_main_menu', construct_main_menu)
