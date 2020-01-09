import sys

import django

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

DJ18 = django.VERSION[:2] == (1, 8)

if PY2:
    from urllib import unquote_plus  # NOQA
else:
    from urllib.parse import unquote_plus  # NOQA


class MiddlewareMixin(object):
    pass