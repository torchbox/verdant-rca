from __future__ import division # Use true division
from django_embedly.templatetags.embed_filters import embedly_get_dict


def media_to_frontend_html(url):
    embed = embedly_get_dict(url)
    if embed is not None:
        # Work out ratio
        ratio = str(embed['height'] / embed['width'] * 100) + "%"

        # Build html
        return '<div style="padding-bottom: %s;" class="responsive-object">%s</div>' % (ratio, embed['html'])
    else:
        return ''


def media_to_editor_html(url):
    embed = embedly_get_dict(url, maxwidth=600)
    if embed is not None:
        # Build html
        extra_attributes = 'contenteditable="false" data-embedtype="media" data-url="%s"' % (url, )
        return '<div contenteditable="false" data-embedtype="media" data-url="%s" style="width: 600px;">%s</div>' % (url, embed['html'])
    else:
        return ''