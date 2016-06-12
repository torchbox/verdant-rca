from django.core.management.base import BaseCommand, CommandError
from twitter.tasks import *


class Command(BaseCommand):
    def handle(self, *args, **options):
        get_tweets_for_all()
