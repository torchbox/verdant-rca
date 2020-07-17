import csv
from collections import defaultdict
from functools import wraps
from optparse import make_option

from bs4 import BeautifulSoup
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailcore.models import Page, get_page_models

HEADING_TAGS = [
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
]

TAGS_REMOVE_EMPTY = ["a"] + HEADING_TAGS

VOID_ELEMENTS = [
    "br",
    "embed",
    "hr",
    "img",
]

TEST_HTML = '''
<h1 class="empty-heading"></h1>
<h2 class="empty-heading"></h2>
<h3 class="empty-heading"></h3>
<h4 class="empty-heading"></h4>
<h5 class="empty-heading"></h5>
<h6 class="empty-heading"></h6>

<h1>has some text content</h1>
<h2>has some text content</h2>
<h3>has some text content</h3>
<h4>has some text content</h4>
<h5>has some text content</h5>
<h6>has some text content</h6>

<h1 class="heading-with-void"><img src="http://imagesource.com" /></h1>
<h2 class="heading-with-void"><embed alt="An example wagtail embed" embedtype="image" /></h2>
<h3 class="heading-with-void"><br/><h3>
<h4 class="heading-with-void"><hr/><h4>
'''

def memoize(function):
    memo = {}
    @wraps(function)
    def wrapper(*args):
        try:
            return memo[args]
        except KeyError:
            rv = function(*args)
            memo[args] = rv
            return rv
    return wrapper


def tag_has_no_text(tag):
    return len(tag.get_text(strip=True)) == 0


def tag_has_void_elements(tag):
    return tag.find_all(VOID_ELEMENTS)


# TODO: is there a cleaner way to make sure html, head and body
# are not appended to richtext html?
def remove_html_wrappers(soup):
    soup.body.unwrap()
    soup.html.unwrap()
    soup.head.decompose()

@memoize
def get_class_richtext_fields(page_class):
        return [
            f.name for f in page_class._meta.fields
            if issubclass(f.__class__, RichTextField)
        ]


def list_all_richtext_fields():
    for content_class in get_page_models():
        richtext_fields = get_class_richtext_fields(content_class)
        if richtext_fields:
            print(content_class.__name__)
            for f in richtext_fields:
                print("    " + f)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--fix',
            action='store_true',
            dest='fix',
            default=False,
            help="Fix any issues found by this script"
        ),
        make_option('--verbose',
            action='store_true',
            dest='verbose',
            default=False,
            help="Verbose output"
        ),
        make_option('--silent',
            action='store_true',
            dest='silent',
            default=False,
            help="Silence all output"
        ),
        make_option('--list-fields',
            action='store_true',
            dest='list_fields',
            default=False,
            help="Only list rich text fields, do not process"
        ),
        make_option(
            '--limit',
            dest='limit',
            default=None,
            help="Limit number of pages sanitised."
        ),
        make_option(
            '--page-ids',
            dest='page_ids',
            default=None,
            help="Specify range of pages (eg 1-20 or 1,2,10) to process"
        ),
        make_option('--csv',
            action='store_true',
            dest='csv',
            default=False,
            help="Output the resulting alterations in CSV format."
        ),
    )

    def __init__(self):
        self.tags_removed = defaultdict(dict)
        self.tags_unwrapped = defaultdict(dict)
        self.pages_processed = 0
        self.pages_urls = {}
        self.page_not_saved = {}
        self.verbose = False

    def log_alterations(self, page, field, tags_removed, tags_unwrapped):
        if tags_removed:
            self.tags_removed[page.id][field] = tags_removed
        if tags_unwrapped:
            self.tags_unwrapped[page.id][field] = tags_unwrapped
        # Save a dictionary of page id/url for use in reporting
        self.pages_urls[page.id] = page.url

    def remove_page_from_log(self, page):
        self.tags_removed.pop(page.id, None)
        self.tags_unwrapped.pop(page.id, None)
        self.page_not_saved[page.id] = page.url

    def remove_empty_tags(self, page, field):
        html = getattr(page, field)
        soup = BeautifulSoup(html, "html5lib")

        potentially_empty_tags = soup.find_all(TAGS_REMOVE_EMPTY)

        tags_removed = []
        tags_unwrapped = []

        for tag in potentially_empty_tags:
            if tag_has_no_text(tag):
                if not tag.descendants:
                    # Its genuinely empty so can remove
                    tags_removed.append(str(tag))
                    tag.decompose()
                elif tag.name in HEADING_TAGS:
                    if tag_has_void_elements(tag):
                        # This is a heading that contains a void element ie img/embed
                        # so just remove wrapping heading element
                        tags_unwrapped.append(str(tag))
                        tag.unwrap()
                    else:
                        # Heading has valid descendants but no text to display
                        tags_removed.append(str(tag))
                        tag.decompose()

        remove_html_wrappers(soup)
        setattr(page, field, soup)
        # setattr(page, field, soup.encode('utf-8'))
        self.log_alterations(page, field, tags_removed, tags_unwrapped)

        return page

    def output_to_csv(self, filename, affected_content):
        headings = ['Page ID', 'Rich Text Field', 'Tags Affected', 'Page URL']
        with open(filename, "wb") as f:
            w = csv.writer(f)
            w.writerow(headings)
            fields = affected_content.values()[0].keys()
            for page_id in affected_content.keys():
                # from pudb import set_trace; set_trace()
                for field in affected_content[page_id]:
                    alterations = [
                        str(affected_content[page_id].get(field, ''))
                        for field in fields
                    ]
                    page_url = self.pages_urls[page_id]
                    row = [page_id, field, alterations, page_url]
                    w.writerow(row)

    def process_page(self, page, richtext_fields):
        self.pages_processed += 1
        if self.verbose:
            print("Page {}".format(page.id))
        for field in richtext_fields:
            page = self.remove_empty_tags(page, field)
        return page

    def handle(self, **options):
        fix = options["fix"]
        list_fields = options["list_fields"]
        limit = options["limit"]
        output_csv = options["csv"]
        page_ids = []
        if options["page_ids"]:
            if "-" in options["page_ids"]:
                page_ids = options["page_ids"].split('-')
                first_id = int(page_ids[0])
                last_id = int(page_ids[1]) + 1
                page_ids = range(first_id, last_id)
            else:
                page_ids = [int(pid) for pid in options["page_ids"].split(',')]
        silent = options["silent"]
        if not silent:
            self.verbose = options["verbose"]

        # Only list the rich text fields on each page type
        if list_fields:
            list_all_richtext_fields()
            return

        # Process specified pages
        if page_ids:
            pages = Page.objects.filter(pk__in=page_ids)
            pages = pages.public().live().specific()
            for page in pages:
                richtext_fields = get_class_richtext_fields(page.__class__)
                page = self.process_page(page, richtext_fields)
                if fix:
                    try:
                        page.save()
                    except ValidationError:
                        self.remove_page_from_log(page)

        # Iterate through all page types and process their richtext fields
        else:
            for content_class in get_page_models():
                richtext_fields = get_class_richtext_fields(content_class)
                if not richtext_fields:
                    continue
                pages = content_class.objects.public().live().specific()

                if limit:
                    pages = pages[:limit]

                if self.verbose:
                    print("{}: {}".format(
                        content_class.__name__,
                        str(richtext_fields))
                    )

                for page in pages:
                    page = self.process_page(page, richtext_fields)
                    if fix:
                        try:
                            page.save()
                        except ValidationError:
                            self.remove_page_from_log(page)

        # Report affected pages
        if self.verbose:
            print("=====================")

        if not silent:
            print("{} pages were processed".format(self.pages_processed))
            print("Tags were removed from richtext on {} pages".format(
                len(self.tags_removed))
            )
            print("Tags were unwrapped within richtext on {} pages".format(
                len(self.tags_unwrapped))
            )
            if self.page_not_saved:
                print("\nThe following pages could not be saved due to validation errors")
                for page_id in self.page_not_saved:
                    print("{}: {}".format(page_id, self.page_not_saved[page_id]))

        # Export reports as CSVs
        if output_csv:
            if self.tags_removed:
                self.output_to_csv(
                    "richtext_tags_removed.csv",
                    self.tags_removed
                )
            if self.tags_unwrapped:
                self.output_to_csv(
                    "richtext_tags_unwrapped.csv",
                    self.tags_unwrapped
                )
            if self.page_not_saved:
                filename = "unsaved_pages.csv"
                headings = ['Page ID', 'Page URL']
                with open(filename, "wb") as f:
                    w = csv.writer(f)
                    w.writerow(headings)
                    for page_id in self.page_not_saved:
                        page_url = self.page_not_saved[page_id]
                        row = [page_id, page_url]
                        w.writerow(row)
