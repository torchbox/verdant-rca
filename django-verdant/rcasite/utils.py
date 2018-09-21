from django.conf import settings

from rca_show.utils import get_base_show_template


def offline_context():
    """
    We use dynamic base template for some RCA Show templates,
    so we need to pass correct base_template into context
    during offline compression.
    """

    for year in [2014, 2015, 2016, 2017, 2018]:
        yield {
            'STATIC_URL': settings.STATIC_URL,
            'base_template': get_base_show_template(year),
        }
