from __future__ import division # Use true division
from django_embedly.templatetags.embed_filters import embedly_get_dict


def editor_attibutes(url):
    return 'contenteditable="false" data-embedtype="media" data-url="%s"' % (url, )


def media_to_html(url, extra_attributes):
    embed = embedly_get_dict(url)
    if embed is not None:
    	# Work out ratio
    	ratio = str(embed['height'] / embed['width'] * 100) + "%"

    	# Build html
    	return '<div class="responsive-object" style="padding-bottom: %s;" %s>%s</div>' % (ratio, extra_attributes, embed['html'])
    else:
    	return ''


def media_to_editor_html(url):
    return media_to_html(url, editor_attibutes(url))