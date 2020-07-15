import logging

from django.core.exceptions import ValidationError
from django.core.management import BaseCommand

from rca.navigation import Navigation, CantPullFromRcaApi

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fetches data for the navigation elements from the new rebuild site"

    def handle(self, **options):
        try:
            logger.info(
                "Fetching navigation data from rebuild site"
            )
            Navigation().get_navigation_data()
        except ValidationError:
            logger.exception("Failed to fetch navigation data")