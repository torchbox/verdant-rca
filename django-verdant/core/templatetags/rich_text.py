from django import template
from django.utils.safestring import mark_safe

from core.rich_text import to_template_html

register = template.Library()

@register.filter
def richtext(value):
    return mark_safe(to_template_html(value))
