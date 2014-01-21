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
def top_menu(context, parent):
	menuitems = parent.get_children().filter(live=True, show_in_menus=True)
	for menuitem in menuitems:
		menuitem.show_dropdown = has_menu_children(menuitem)
	return {
    	'menuitems': menuitems,
    	'request': context['request'],
    }

@register.inclusion_tag('demo/tags/top_menu_children.html', takes_context=True)
def top_menu_children(context, parent):
	menuitems_children = parent.get_children().filter(live=True, show_in_menus=True)
	return {
		'parent': parent,
    	'menuitems_children': menuitems_children,
    	'request': context['request'],
    }