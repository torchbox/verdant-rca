from django.core.management.base import BaseCommand

from rca.models import StandardPage, StandardIndex

from shortcourses.models import ShortCoursePage


class Commmand(BaseCommand):
    """
    Migrates short course data from standard pages to short course pages.
    """

    def add_arguments(self, parser):
        parser.add_argument('parent_page_id', help='The ID of the parent index page to migrate courses under')

    def handle(self, *args, **options):
        parent_page_id = options['parent_page_id']
        parent_page = StandardIndex.objects.get(id=parent_page_id)

        for standard_page in parent_page.objects.get_children():
            short_course = ShortCoursePage()
            # https://github.com/wagtail/wagtail/blob/master/wagtail/core/models.py#L1046
