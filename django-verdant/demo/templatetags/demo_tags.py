from django import template
from demo.models import *

register = template.Library()


@register.assignment_tag(takes_context=True)
def get_site_root(context):
    return context['request'].site.root_page

def has_menu_children(page):
	if page.get_children().filter(live=True, show_in_menus=True):
		return True;
	else:
		return False;

@register.inclusion_tag('demo/tags/top_menu.html', takes_context=True)
def top_menu(context, parent, calling_page=None):
	menuitems = parent.get_children().filter(live=True, show_in_menus=True)
	for menuitem in menuitems:
		menuitem.show_dropdown = has_menu_children(menuitem)
	return {
		'calling_page': calling_page,
    	'menuitems': menuitems,
    	'request': context['request'], #required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('demo/tags/top_menu_children.html', takes_context=True)
def top_menu_children(context, parent):
	menuitems_children = parent.get_children().filter(live=True, show_in_menus=True)
	return {
		'parent': parent,
    	'menuitems_children': menuitems_children,
    	'request': context['request'], #required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('demo/tags/secondary_menu.html', takes_context=True)
def secondary_menu(context, calling_page=None):
    if calling_page:
        pages = calling_page.get_children().filter(live=True, show_in_menus=True)

        # If no children, get siblings instead
        if len(pages) == 0:
            pages = calling_page.get_other_siblings().filter(live=True, show_in_menus=True)
    return {
        'pages': pages,
        'request': context['request'],  #required by the {% pageurl %} tag that we want to use within this template
    }
# To do: make relevant pages extend EditorialPage so that we can show the listing intro too
@register.inclusion_tag('demo/tags/standard_index_listing.html', takes_context=True)
def standard_index_listing(context, calling_page):
    pages = Page.objects.filter(path__startswith=calling_page.path).filter(depth=calling_page.depth+1).filter(live=True)
    return {
        'pages': pages,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }