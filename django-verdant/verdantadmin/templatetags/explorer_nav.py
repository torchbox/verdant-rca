from django import template

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
