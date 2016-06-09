import csv

from django.core.management.base import BaseCommand
from django.db import models

from rca.models import NewStudentPage
from rca.utils import convert_degree_filters


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help="Don't perform any action",
        )

    def handle(self, filename, **options):
        q = models.Q(in_show=True)
        q &= models.Q(graduation_year=2016)
        q &= models.Q(programme__in=['fashionmenswear', 'fashionwomenswear'])

        final_q = models.Q()
        final_q |= convert_degree_filters(q, 'ma')
        final_q |= convert_degree_filters(q, 'mphil')
        final_q |= convert_degree_filters(q, 'phd')
        students = NewStudentPage.objects.filter(final_q)

        # Publish them
        for student in students:

            # Find latest revision that is in moderation
            revision = student.revisions.filter(submitted_for_moderation=True).order_by('-created_at').first()

            if not revision:
                print "NOT IN MODERATION:", student.id
                continue

            # Check it's valid
            page = revision.as_page_object()
            error = False

            if not page.programme:
                print "NOT SET PROGRAMME:", student.id
                error = True

            if not page.school:
                print "NOT SET SCHOOL:", student.id
                error = True

            if not page.get_profile() or not page.get_profile()['graduation_year']:
                print "NOT SET GRADUATION YEAR:", student.id
                error = True

            # Skip if error found
            if error:
                continue

            if options['dry-run'] is False:
                # Publish!
                revision.publish()
                print "PUBLISHED:", student.id
            else:
                print "WOULD PUBLISH:", student.id
