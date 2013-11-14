from __future__ import division # Use true division
from django_embedly.templatetags.embed_filters import embedly_get_dict
from django.utils.html import escape


def media_to_frontend_html(url):
    embed = embedly_get_dict(url)
    if embed is not None:
        # Work out ratio
        if embed['width'] and embed['height']:
            ratio = str(embed['height'] / embed['width'] * 100) + "%"
        else:
            ratio = "0"

        # Build html
        return '<div style="padding-bottom: %s;" class="responsive-object">%s</div>' % (ratio, embed['html'])
    else:
        return ''


def media_to_editor_html(url):
    # Check that the media exists
    embed = embedly_get_dict(url)
    if embed is None:
        return ''
    return '<div class="media-placeholder" contenteditable="false" data-embedtype="media" data-url="%s"><h3>%s</h3><p>%s</p><img src="%s"></div>' % (url, escape(embed['title']), url, embed['thumbnail_url'])