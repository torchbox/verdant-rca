from django.conf import settings

from rca_show.models import ShowIndexPage
from rca_show.utils import get_base_show_template


def offline_context():
    """
    We use dynamic base template for some RCA Show templates,
    so we need to pass correct base_template into context
    during offline compression.
    """

    years = ShowIndexPage.objects.order_by().values_list('year', flat=True).distinct()

    for year in years:
        yield {
            'STATIC_URL': settings.STATIC_URL,
            'base_template': get_base_show_template(year),
        }
