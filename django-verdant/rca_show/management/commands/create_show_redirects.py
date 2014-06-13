from django.core.management.base import BaseCommand

from wagtail.wagtailredirects.models import Redirect

from rca_show.models import ShowIndexPage


class Command(BaseCommand):
    def handle(self, show_index_id, **options):
        # Find show index page
        show_index = ShowIndexPage.objects.get(id=show_index_id)

        for student in show_index.get_students():
            # Work out a URL to redirect from
            from_url = show_index.url + student.slug + '/'

            # Find students url inside 
            if show_index.is_programme_page:
                to_url = show_index.reverse_subpage('student', programme=student.programme, slug=student.slug)
            else:
                to_url = show_index.reverse_subpage('student', school=student.school, programme=student.programme, slug=student.slug)

            # Make sure the URLs are different (so we don't make any unneeded redirects)
            if from_url != to_url:
                # Normalise the URL
                from_url_normalised = Redirect.normalise_path(from_url)

                # Create the redirect
                redirect, created = Redirect.objects.get_or_create(old_path=from_url_normalised, defaults={'redirect_link': to_url})

                # Print message
                if created:
                    print "Created redirect: " + from_url_normalised
