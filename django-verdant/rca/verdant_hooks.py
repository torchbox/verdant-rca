from verdantadmin import hooks
from verdantadmin.menu import MenuItem

def user_is_student(user):
    return [group.name for group in user.groups.all()] == ['Students']

def construct_main_menu(request, menu_items):
    if user_is_student(request.user):
        pass
        #menu_items.append(
        #    MenuItem('Ponies', '/ponies/')
        #)

hooks.register('construct_main_menu', construct_main_menu)
