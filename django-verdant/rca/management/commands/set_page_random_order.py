import random
import inspect
from django.core.management.base import NoArgsCommand
from rca import models


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        # Initialise random number generator (this sets the seed to the system time)
        random.seed(None)

        # get classes which have a random_order field
        classes = [
            m[1] for m in inspect.getmembers(models, inspect.isclass)
            if hasattr(m[1], "_meta") and [f for f in m[1]._meta.fields if f.name == "random_order"]
        ]

        for klass in classes:
            # Loop through objects and set random_order
            for obj in klass.objects.all():
                obj.random_order = random.randrange(100000)
                obj.save(update_fields=['random_order'])
