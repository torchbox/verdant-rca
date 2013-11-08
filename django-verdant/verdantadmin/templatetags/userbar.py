from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def userbar(context):
    try:
        items = ''.join(["<li>%s</li>" % item for item in context['request'].userbar])
        return """<ul class="verdant-user-bar">%s</ul>""" % items
    except AttributeError:
        return ''
