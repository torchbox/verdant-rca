import json
from optparse import make_option

from django.core.management.base import BaseCommand
from modelcluster.models import model_from_serializable_data
from wagtail.wagtailcore.models import get_page_models


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--fix',
            action='store_true',
            dest='fix',
            default=False,
            help="Fix any issues found by this script"
        ),
        make_option('--list-fields',
            action='store_true',
            dest='list_fields',
            default=False,
            help="Fix any issues found by this script"
        ),
    )

    @staticmethod
    def get_class_richtext_fields(page_class):
        return [
            f.name for f in page_class._meta.fields
            if f.__class__.__name__ == "RichTextField"
        ]

    def handle(self, fix=False, **options):
        for page_class in get_page_models():

            if options["list_fields"]:
                richtext_fields = self.get_class_richtext_fields(page_class)
                if richtext_fields:
                    print(page_class.__name__)
                    for f in richtext_fields:
                        print("    " + f)
