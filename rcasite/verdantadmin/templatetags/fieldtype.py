from django import template

from core.util import camelcase_to_underscore

register = template.Library()

@register.filter
def fieldtype(bound_field):
    return camelcase_to_underscore(bound_field.field.__class__.__name__)
