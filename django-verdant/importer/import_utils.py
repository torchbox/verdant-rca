#from lxml import etree as ET
import html2text
import markdown
from django.utils.text import slugify


def text_from_elem(parent, elemname, **kwargs):
    """
        Returns the text content of an xml element.
        Kwargs:
            textify (bool): strip html tags,
            length (int): trim to max length for db field compatibility
    """
    textify = kwargs.get('textify', False)
    length = kwargs.get('length', False)
    h = html2text.HTML2Text()
    h.body_width = 0
    error = None

    elem = parent.find(elemname)
    if elem is not None:
        text = elem.text or ''
        if text:
            text = text.strip()
            if textify:
                text = h.handle(text).strip()
            if length:
                text, error = checklength(text, length)
    else:
        text = ''
    return (text, error)


def richtext_from_elem(elem, **kwargs):
    """
        Returns html-formatted string from an xml element.
        Kwargs:
            prefix (str): e.g. '##' for making a <h2> element
    """
    prefix = kwargs.get('prefix', '')
    h = html2text.HTML2Text()
    h.body_width = 0
    text = elem.text or ''
    text = text.strip()
    if '<p>' in text:
        html = markdown.markdown(prefix + h.handle(text))
    else:
        html = markdown.markdown(prefix + text)
    return html


def makeslug(obj):
    """
        Converts an object's title to a slug, checking for uniqueness first,
        appending '-1' etc if necessary.
    """
    potentialslug = slugify(unicode(obj.title))[0:50]
    # check for slug uniqueness
    increment = 1
    while obj.__class__.objects.filter(slug=potentialslug).count():
        increment += 1
        potentialslug = potentialslug[0:49-len(str(increment))] + "-" + str(increment)
    return potentialslug


def checklength(text, length):
    error = None
    if text and len(text) > length:
        error = u'Text clipped from "\u2026%(orig)s" to: "\u2026%(new)s"' % {
                'orig': text[length-25:],
                'new': text[length-25:length],
                }
        text = text[0:length]
    return (text, error)
