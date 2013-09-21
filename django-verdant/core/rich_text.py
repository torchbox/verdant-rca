from bs4 import BeautifulSoup, NavigableString, Tag
from urlparse import urlparse
import re  # parsing HTML with regexes LIKE A BOSS.

# FIXME: we don't really want to import verdantimages within core.
# For that matter, we probably don't want core to be concerned about translating
# HTML for the benefit of the hallo.js editor...
from verdantimages.models import Image
from verdantimages.formats import FORMATS_BY_NAME

from core.models import Page


ALLOWED_URL_SCHEMES = ['', 'http', 'https', 'ftp', 'mailto', 'tel']

def url_is_permitted(url_string):
    # TODO: more paranoid checks (urlparse doesn't catch "jav\tascript:alert('XSS')")
    url = urlparse(url_string)
    return (url.scheme in ALLOWED_URL_SCHEMES)

WHITELIST_RULES = {
    '[document]': [],
    'a': {'href': url_is_permitted},
    'b': [],
    'br': [],
    'div': [],
    'em': [],
    'h1': [], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': [],
    'i': [],
    'img': {'src': url_is_permitted, 'width': True, 'height': True, 'alt': True},
    'li': [],
    'ol': [],
    'p': [],
    'strong': [],
    'sub': [],
    'sup': [],
    'ul': [],
}


def filter_a_for_db(elem):
    if 'data-id' in elem.attrs:
        strip_attributes_not_in_list(elem, ['data-id'])
    else:
        strip_attributes_not_in_list(elem, ['href'])

def filter_img_for_db(elem):
    if 'data-id' in elem.attrs:
        strip_attributes_not_in_list(elem, ['data-id', 'data-format', 'alt'])
    else:
        strip_attributes_not_in_list(elem, ['href', 'width', 'height', 'alt'])

DB_WHITELIST_RULES = WHITELIST_RULES.copy()
DB_WHITELIST_RULES.update({
    'a': filter_a_for_db,
    'img': filter_img_for_db,
})


def filter_a_for_editor(elem):
    strip_attributes_not_in_list(elem, ['href', 'data-id'])
    if 'data-id' in elem.attrs:
        try:
            page = Page.objects.get(id=elem.attrs['data-id'])
            elem['href'] = page.url
        except Page.DoesNotExist:
            pass

def filter_img_for_editor(elem):
    strip_attributes_not_in_list(elem, ['src', 'data-id', 'data-format', 'width', 'height', 'alt'])
    populate_image_attrs(elem)

EDITOR_WHITELIST_RULES = WHITELIST_RULES.copy()
EDITOR_WHITELIST_RULES.update({
    'a': filter_a_for_editor,
    'img': filter_img_for_editor,
})


def strip_attributes_not_in_list(elem, allowed_attrs):
    for attr in elem.attrs.keys():
        if attr not in allowed_attrs:
            del elem[attr]


def populate_image_attrs(elem):
    """
    populate src, width, height and class attributes
    from the 'data-id' and 'data-format' attributes
    """
    if 'data-id' in elem.attrs:
        try:
            image = Image.objects.get(id=elem.attrs['data-id'])
            try:
                format_name = elem.attrs['data-format']
                format = FORMATS_BY_NAME[format_name]
                filter_spec = format.filter_spec
                classnames = format.classnames
            except KeyError:
                filter_spec = 'max-1024x768'
                classnames = None

            rendering = image.get_rendition(filter_spec)
            elem['src'] = rendering.url
            elem['width'] = rendering.width
            elem['height'] = rendering.height

            if classnames:
                elem['class'] = classnames
            else:
                try:
                    del elem['class']
                except KeyError:
                    pass

        except Image.DoesNotExist:
            pass


def apply_whitelist(doc, rules):
    if isinstance(doc, NavigableString):
        return
    elif isinstance(doc, Tag):
        for child in doc.contents:
            apply_whitelist(child, rules)

        element_rule = rules.get(doc.name)

        if element_rule is None:
            # don't recognise this tag name, so KILL IT WITH FIRE
            doc.unwrap()

        elif callable(element_rule):
            element_rule(doc)

        elif isinstance(element_rule, list):
            # rule is a list of allowed attributes
            strip_attributes_not_in_list(doc, element_rule)

        elif isinstance(element_rule, dict):
            for attr in doc.attrs.keys():
                attr_rule = element_rule.get(attr)
                if callable(attr_rule):
                    attr_is_allowed = attr_rule(doc[attr])
                else:
                    attr_is_allowed = attr_rule

                if not attr_is_allowed:
                    del doc[attr]

        else:
            raise TypeError("Don't know how to handle %r as a whitelist rule" % element_rule)

    else:
        doc.decompose()  # don't know what type of object this is, so KILL IT WITH FIRE


def to_db_html(html):
    doc = BeautifulSoup(html)
    apply_whitelist(doc, DB_WHITELIST_RULES)
    return unicode(doc)

def to_editor_html(html):
    doc = BeautifulSoup(html)
    apply_whitelist(doc, EDITOR_WHITELIST_RULES)
    return unicode(doc)

FIND_A_TAG = re.compile(r'<a(\b[^>]*)>')
FIND_IMG_TAG = re.compile(r'<img(\b[^>]*)>')
FIND_ATTRS = re.compile(r'([\w-]+)\=("[^"]*"|\'[^\']*\'|\S*)')
FIND_QUOTED_TOKEN = re.compile(r'[\'\"]?([\w-]*)')

def to_template_html(html):
    def extract_attrs(attr_string, whitelist):
        attributes = {}
        for name, val in FIND_ATTRS.findall(attr_string):
            if name in whitelist:
                attributes[name] = val
        return attributes

    def build_tag(name, attributes):
        return '<' + name + ''.join([" %s=%s" % i for i in attributes.items()]) + '>'

    def get_attr_token(s):
        clean_val = FIND_QUOTED_TOKEN.match(s)
        return (clean_val and clean_val.group(1))

    def replace_a_elem(m):
        attributes = extract_attrs(m.group(1), ('data-id', 'href'))

        if 'data-id' in attributes:
            try:
                page_id = get_attr_token(attributes['data-id'])
                page = Page.objects.get(id=page_id)
                attributes['href'] = page.url
            except Page.DoesNotExist:
                pass
            del attributes['data-id']

        return build_tag('a', attributes)

    def replace_img_elem(m):
        attributes = extract_attrs(m.group(1), ('data-id', 'data-format', 'src', 'width', 'height', 'alt', 'class'))

        if 'data-id' in attributes:
            try:
                image_id = get_attr_token(attributes['data-id'])
                image = Image.objects.get(id=image_id)
                try:
                    format_name = get_attr_token(attributes['data-format'])
                    format = FORMATS_BY_NAME[format_name]
                    filter_spec = format.filter_spec
                    classnames = format.classnames
                except KeyError:
                    filter_spec = 'max-1024x768'
                    classnames = None

                rendering = image.get_rendition(filter_spec)
                attributes['src'] = rendering.url
                attributes['width'] = rendering.width
                attributes['height'] = rendering.height

                if classnames:
                    attributes['class'] = classnames
                else:
                    try:
                        del attributes['class']
                    except KeyError:
                        pass

            except Image.DoesNotExist:
                pass

        return build_tag('img', attributes)


    html = FIND_A_TAG.sub(replace_a_elem, html)
    html = FIND_IMG_TAG.sub(replace_img_elem, html)
    return html
