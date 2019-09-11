from csv import DictReader

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.six.moves.urllib.parse import urlparse

from wagtail.wagtailcore.models import Site, Page
from wagtail.wagtailredirects.models import Redirect


def get_page_from_path(path):
    """ Takes a full url. Roughly reproduces wagtail.wagtailcore.views.serve.
    """
    parsed_path = urlparse(path)
    try:
        site = Site.objects.get(hostname=parsed_path.netloc)
    except Site.DoesNotExist:
        import pdb; pdb.set_trace()

    path_components = [component for component in parsed_path.path.split('/')
                       if component]
    page = site.root_page
    while path_components:
        child_slug = path_components[0]
        path_components = path_components[1:]
        page = page.get_children().get(slug=child_slug)
    return page


class Command(BaseCommand):
    help = "Creates Wagtail redirects from a csv with a 'from' and 'to' "
    "column, where entries are URLs with domains."

    def add_arguments(self, parser):
        parser.add_argument('file_path', help="Path to a csv file")
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--from-header', default='from',
                            help="Header for old-path column if not 'from'")
        parser.add_argument('--to-header', default='to',
                            help="Header for new-path column if not 'to'")

    def handle(self, *args, **options):
        file_path = options['file_path']
        dry_run = options['dry_run']
        from_header = options['from_header']
        to_header = options['to_header']

        updated_count = 0
        created_count = 0
        error_count = 0
        local_netloc = True

        with open(file_path, 'r') as f:
            reader = DictReader(f)

            for row in reader:
                old_path = row[from_header]
                new_path = row[to_header]

                if old_path and new_path:

                    # urlparse requires at least a '//' to avoid identifying the
                    # domain as a path component
                    if '//' not in old_path:
                        old_path = '//' + old_path

                    netloc = urlparse(old_path).netloc
                    if not netloc:
                        print("Line {} - No domain provided: {}".format(reader.line_num, old_path))
                        continue

                    try:
                        old_site = Site.objects.get(hostname=netloc)
                    except Site.DoesNotExist:
                        print("Line {} - Site does not exist: {}".format(reader.line_num, netloc))
                        error_count += 1
                        continue

                    normalised_path = Redirect.normalise_path(old_path)

                    if len(normalised_path) > 255:
                        print(
                            "Line {} - 'From' path is too long ({} characters, maximum is 255)".format(
                                reader.line_num, len(normalised_path))
                        )
                        error_count += 1
                        continue

                    # We don't use .get_or_create because we want to support the
                    # --dry-run flag
                    with transaction.atomic():
                        try:
                            redirect = Redirect.objects.get(site=old_site,
                                                            old_path=normalised_path)
                            updated_count += 1
                        except Redirect.DoesNotExist:
                            redirect = Redirect(site=old_site,
                                                old_path=normalised_path)
                            created_count += 1

                        try:
                            target_page = get_page_from_path(new_path) #optimally, get Page for redirect
                            if not dry_run:
                                redirect.redirect_page = target_page
                                redirect.save()
                        except Page.DoesNotExist:
                            print("Line {} - Page does not exist: {}. Linking to URL.".format(reader.line_num, new_path))
                            target_url = new_path #else link to URL directly
                            if not dry_run:
                                redirect.redirect_link = target_url
                                redirect.save()
                            continue

        print("\n")
        print("Created: {}".format(created_count))
        print("Updated: {}".format(updated_count))
        print("Errored (so no action taken): {}".format(error_count))
        print("\nDone!")
