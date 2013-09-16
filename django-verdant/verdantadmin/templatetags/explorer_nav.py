from django import template

from core.models import Page

register = template.Library()

@register.inclusion_tag('verdantadmin/shared/explorer_nav.html')
def explorer_nav():
    return {
        'pages': Page.get_first_root_node().get_children()
    }

@register.inclusion_tag('verdantadmin/shared/explorer_nav.html')
def explorer_subnav(pages):
    return {
        'pages': pages
    }
