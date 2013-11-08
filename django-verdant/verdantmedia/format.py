from django_embedly.templatetags.embed_filters import embedly


def editor_attibutes(url):
    return 'data-embedtype="media" data-url="%s"' % (url, )


def media_to_html(url, extra_attributes):
    embedly_html = embedly(url, arg=600)
    if embedly_html != "":
    	return '<div %s>%s</div>' % (extra_attributes, embedly_html)
    else:
    	return ''


def media_to_editor_html(url):
    return media_to_html(url, editor_attibutes(url))