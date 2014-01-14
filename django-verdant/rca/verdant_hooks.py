from verdantadmin import hooks

def construct_main_menu(menu_items):
    pass
    # raise Exception('hello from construct_main_menu!')
hooks.register('construct_main_menu', construct_main_menu)
