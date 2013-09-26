class Format(object):
    def __init__(self, name, label, classnames, filter_spec):
        self.name = name
        self.label = label
        self.classnames = classnames
        self.filter_spec = filter_spec


# TODO: somewhere to configure these on a per-installation (or per-site?) basis
FORMATS = [
    Format('fullwidth', 'Full width', 'full-width', 'width-800'),
    Format('left', 'Left-aligned', 'left', 'width-500'),
    Format('right', 'Right-aligned', 'right', 'width-500'),
]

FORMATS_BY_NAME = {}
for format in FORMATS:
    FORMATS_BY_NAME[format.name] = format
