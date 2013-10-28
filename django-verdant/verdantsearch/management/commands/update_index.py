from django.core.management.base import NoArgsCommand
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from verdantsearch.indexed import Indexed
from verdantsearch.search import Search


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        # Search object
        s = Search()

        # Reset the index
        s.reset_index()

        # Get list of indexed models
        indexed_models = [model for model in models.get_models() if issubclass(model, Indexed)]
        
        # Loop through and add all items of each model into the index
        for model in indexed_models:
            for obj in model.objects.all():
                s.add(obj)

        # Refresh index
        s.refresh_index()
