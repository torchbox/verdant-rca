import re
from django import template
from django.utils.safestring import mark_safe
from verdantembeds.embeds import get_embed


register = template.Library()

EMBED_REGEX = re.compile(r'(https?://[\w\d:#@%/;$()~_?\+\-=\\\.&]+)', re.I)


@register.filter
def embedly(html, arg=None):
    return mark_safe(EMBED_REGEX.sub(lambda x: embed_replace(x.group(1), maxwidth=arg), html))


def embed_replace(url, maxwidth=None):
    embedly = get_embed(url, maxwidth)
    if embedly is not None:
        return embedly['html']
    else:
        return ''