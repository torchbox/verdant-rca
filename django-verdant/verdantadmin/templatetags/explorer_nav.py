from django import template
from django.core import urlresolvers

from core.models import get_navigation_menu_items

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
