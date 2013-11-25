#from lxml import etree as ET
import html2text
import markdown
import re
from bs4 import BeautifulSoup
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
                text, error = check_length(text, length)
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
        if text:
            html = markdown.markdown(prefix + text)
        else:
            html = text
    return html


def make_slug(obj):
    """
        Converts an object's title to a slug, checking for uniqueness first,
        appending '-1' etc if necessary.
    """
    original = slugify(unicode(obj.title))[0:50]
    potentialslug = original
    # check for slug uniqueness
    increment = 1
    while obj.__class__.objects.filter(slug=potentialslug).count():
        if obj.__class__.objects.get(slug=potentialslug) == obj:
            break
        else:
            potentialslug = '-'.join([original[0:49-len(str(increment))],str(increment)])
            increment += 1
    return potentialslug


def check_length(text, length):
    error = None
    if text and len(text) > length:
        error = u'Text clipped from "\u2026%(orig)s" to: "\u2026%(new)s"' % {
                'orig': text[length-25:],
                'new': text[length-25:length],
                }
        text = text[0:length]
    return (text, error)


def mdclean(target):
    """
        Clean text for markdown
        
        Starts and ends of lists:

        >>> mystring = 'hi there\n- list item 1\n- list item 2\nNext paragraph.'
        >>> mdlistify(mystring)
        'hi there\n\n- list item 1\n- list item 2\n\nNext paragraph.'

        Paragraphs:

        >>> mystring = 'Paragraph one.\nParagraph two.\nParagraph three.'
        >>> mdlistify(mystring)
        'Paragraph one.\n\nParagraph two.\n\nParagraph three.'

    """
    # Match first list item and insert line break
    target = re.sub(
            r'(?P<para>(^|\n)[^-*].+)[\n]+(?=[-*])',
            '\g<para>\n\n',
            target
            )
    # Match last list item and insert line break
    target = re.sub(
            r'(?P<listend>(^|\n)[-*].+)[\n]+(?P<para>[^-*])',
            '\g<listend>\n\n\g<para>',
            target
            )
    # Match paragraphs
    target = re.sub(
            r'(?<=(^[^-*].|\n[^-*]))(?P<para1>.+)[\n]+(?=[^-*])',
            '\g<para1>\n\n',
            target
            )
    return target


def statement_extract(statement):
    """
        Extract paragraphs beginning "Supported by:" or "Collaboration:" or "Collaborations:"

        >>> statement_extract('<p>Sample paragraph.</p><p>Second sample.</p><p>Supported by: Rod, Jane, Freddy</p><p>Collaborations: Bill, Ben</p>")
        ('<p>Sample paragraph.</p><p>Second sample.</p>', [u'Rod', u'Jane', u'Freddy'], [u'Bill', u'Ben'])
    """
    soup = BeautifulSoup(statement, 'html.parser')
    supporters = []
    collaborators = []
    for p in soup.find_all('p'):
        text = p.text
        supported = 'Supported by: '
        collaborate = 'Collaboration'

        if text.startswith(supported):
            text = text[len(supported):]
            for entry in text.split(','):
                supporters.append(entry.strip())
            p.decompose()
            continue

        if text.startswith(collaborate):
            text = text[len(collaborate):]
            if text.startswith('s: '):
                text = text[3:]
            if text.startswith(': '):
                text = text[2:]
            for entry in text.split(','):
                collaborators.append(entry.strip())
            p.decompose()
            continue
    return str(soup), supporters, collaborators
