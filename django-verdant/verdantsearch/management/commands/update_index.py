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
            print model._meta.app_label + "." + model.__name__
            object_count = 0
            for obj in model.objects.all():
                object_count += 1
                s.add(obj)
            print "  " + str(object_count) + " objects"

        # Refresh index
        s.refresh_index()
