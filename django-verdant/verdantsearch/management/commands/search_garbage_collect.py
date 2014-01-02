from django.core.management.base import NoArgsCommand
from verdantsearch import models


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        # Clean daily hits
        print "Cleaning daily hits records... ",
        models.SearchTermsDailyHits.garbage_collect()
        print "Done"

        # Clean search terms
        print "Cleaning search terms records... ",
        models.SearchTerms.garbage_collect()
        print "Done"