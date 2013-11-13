from django.core.management.base import NoArgsCommand
import random
from rca.models import StaffPage, ResearchItem


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        # Initialise random number generator (this sets the seed to the system time)
        random.seed(None)

        # Loop through staff and set random_order
        for staff in StaffPage.objects.all():
            staff.random_order = random.randrange(100000)
            staff.save(update_fields=['random_order'])

        # Loop through research items and set random_order
        for researchitem in ResearchItem.objects.all():
            researchitem.random_order = random.randrange(100000)
            researchitem.save(update_fields=['random_order'])