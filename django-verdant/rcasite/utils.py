from django.conf import settings

from rca_show.utils import get_base_show_template


def offline_context():
    """
    We use dynamic base template for some RCA Show templates,
    so we need to pass correct base_template into context
    during offline compression.
    """
    # These years correspond to the years that we have base templates for in `rca_show/templates`
    for year in ['2016', '2017', '2018', '2019']:
        yield {
            'STATIC_URL': settings.STATIC_URL,
            'base_template': get_base_show_template(year),
        }
