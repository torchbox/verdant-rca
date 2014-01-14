from django import template
from django.core import urlresolvers

from core.models import get_navigation_menu_items

from verdantadmin import hooks
from verdantsnippets.permissions import user_can_edit_snippets  # TODO: reorganise into pluggable architecture so that verdantsnippets registers its own menu item

register = template.Library()


@register.inclusion_tag('verdantadmin/shared/explorer_nav.html')
def explorer_nav():
    return {
        'nodes': get_navigation_menu_items()
    }


@register.inclusion_tag('verdantadmin/shared/explorer_nav.html')
def explorer_subnav(nodes):
    return {
        'nodes': nodes
    }


@register.assignment_tag
def get_verdantadmin_tab_urls():
    resolver = urlresolvers.get_resolver(None)
    return [
        (key, value[2].get("title", key))
        for key, value
        in resolver.reverse_dict.items()
        if isinstance(key, basestring) and key.startswith('verdantadmin_tab_')
    ]


@register.inclusion_tag('verdantadmin/shared/main_nav.html', takes_context=True)
def main_nav(context):
    menu_items = []
    for fn in hooks.get_hooks('construct_main_menu'):
        fn(menu_items)

    return {
        'perms': context['perms'],
        'request': context['request'],
        'can_edit_snippets': user_can_edit_snippets(context['request'].user),
    }
