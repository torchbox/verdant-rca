import json
from optparse import make_option

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from modelcluster.models import model_from_serializable_data
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailcore.models import Page, get_page_models
from wagtail.wagtailsnippets.models import get_snippet_models

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


def get_class_richtext_fields(page_class):
        return [
            f.name for f in page_class._meta.fields
            if issubclass(f.__class__, RichTextField)
        ]


# WARNING: for development use only
def get_single_example_page():
        # return Page.objects.get(pk=18797).specific
        return Page.objects.get(pk=17272).specific


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
            help="Fix any issues found by this script"
        ),
        make_option('--list-fields',
            action='store_true',
            dest='list_fields',
            default=False,
            help="Fix any issues found by this script"
        ),
        make_option(
            '--limit',
            dest='limit',
            default=None,
            help="Limit number of pages sanitised."
        ),
    )

    def __init__(self):
        self.tags_removed = []
        self.tags_unwrapped = []

    def remove_empty_tags(self, html):
        soup = BeautifulSoup(html, "html5lib")
        potentially_empty_tags = soup.find_all(TAGS_REMOVE_EMPTY)

        for tag in potentially_empty_tags:
            if tag_has_no_text(tag):
                if not tag.descendants:
                    # Its genuinely empty so can remove
                    self.tags_removed.append(str(tag))
                    tag.decompose()
                elif tag.name in HEADING_TAGS:
                    if tag_has_void_elements(tag):
                        # This is a heading that contains a void element ie img/embed
                        # so just remove wrapping heading element
                        self.tags_unwrapped.append(str(tag))
                        tag.unwrap()
                    else:
                        # Heading has valid descendants but no text to display
                        self.tags_removed.append(str(tag))
                        tag.decompose()

        remove_html_wrappers(soup)
        return str(soup)

    def handle(self, fix=False, **options):
        list_fields = options["list_fields"]
        verbose = options["verbose"]
        for content_class in get_page_models() + get_snippet_models():

            if list_fields:
                richtext_fields = get_class_richtext_fields(content_class)
                if richtext_fields:
                    print(content_class.__name__)
                    for f in richtext_fields:
                        print("    " + f)


        # page = get_single_example_page()
        # print(page.body)
        # print(" DEBUG ")
        # print(self.remove_empty_tags(page.body))

        print(self.remove_empty_tags(TEST_HTML))

        if verbose:
            print(" DEBUG ")
            print("Tags removed:")
            for t in self.tags_removed:
                print(t)
