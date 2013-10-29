from django.core.management.base import NoArgsCommand
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from verdantsearch.indexed import Indexed
from verdantsearch.search import Search


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        # Print info
        print "Getting object list"

        # Get list of indexed models
        indexed_models = [model for model in models.get_models() if issubclass(model, Indexed) and model.indexed]

        # Object set
        object_set = {}

        # Add all objects to object set and detect any duplicates
        # Duplicates are caused when both a model and a derived model are indexed
        # Eg, StudentPage inherits from Page and both of these models are indexed
        # If we were to add all objects from both models into the index, all the StudentPages will have two entries
        for model in indexed_models:
            print model.__name__
            # Get toplevel content type
            toplevel_content_type = model.get_toplevel_content_type()

            # Loop through objects
            for obj in model.objects.all():
                # Get key for this object
                key = toplevel_content_type + ":" + str(obj.pk)

                # Check if this key already exists
                if key in object_set:
                    # Conflict, work out who should get this space
                    # The object with the longest content type string gets the space
                    # Eg, "core.Page-rca.StudentPage" kicks out "core.Page"
                    if len(obj.get_content_type()) > len(object_set[key].get_content_type()):
                        # Take the spot
                        object_set[key] = obj
                else:
                    # Space free, take it
                    object_set[key] = obj

        # Search object
        s = Search()

        # Reset the index
        print "Reseting index"
        s.reset_index()

        # Add objects to index
        print "Adding objects"
        s.add_bulk(object_set.values())

        # Refresh index
        print "Refreshing index"
        s.refresh_index()
