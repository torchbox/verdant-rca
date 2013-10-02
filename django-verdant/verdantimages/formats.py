from django.conf import settings
from django.utils.importlib import import_module

class Format(object):
    def __init__(self, name, label, classnames, filter_spec):
        self.name = name
        self.label = label
        self.classnames = classnames
        self.filter_spec = filter_spec


FORMATS = []
FORMATS_BY_NAME = {}

def register_image_format(format):
    if format.name in FORMATS_BY_NAME:
        raise KeyError("Image format '%s' is already registered" % format.name)
    FORMATS_BY_NAME[format.name] = format
    FORMATS.append(format)

def unregister_image_format(format_name):
    # handle being passed a format object rather than a format name string
    try:
        format_name = format_name.name
    except AttributeError:
        pass

    try:
        del FORMATS_BY_NAME[format_name]
        FORMATS = [fmt for fmt in FORMATS if fmt.name != format_name]
    except KeyError:
        raise KeyError("Image format '%s' is not registered" % format_name)

def get_image_formats():
    search_for_image_formats()
    return FORMATS

def get_image_format(name):
    return FORMATS_BY_NAME[name]

_searched_for_image_formats = False
def search_for_image_formats():
    global _searched_for_image_formats
    if not _searched_for_image_formats:
        for app_module in settings.INSTALLED_APPS:
            try:
                import_module('%s.image_formats' % app_module)
            except ImportError:
                continue

        _searched_for_image_formats = True


# Define default image formats
register_image_format(Format('fullwidth', 'Full width', 'full-width', 'width-800'))
register_image_format(Format('left', 'Left-aligned', 'left', 'width-500'))
register_image_format(Format('right', 'Right-aligned', 'right', 'width-500'))
