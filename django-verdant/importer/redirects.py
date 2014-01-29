from data.redirects import REDIRECTS
from wagtail.wagtailredirects.models import Redirect
from wagtail.wagtailcore.models import Site, Page


class RedirectsImporter(object):
    def __init__(self, site=None):
        if site is None:
            site = Site.objects.get(is_default_site=True)
        self.site = site

    def find_page_from_url(self, current_page, path_components=[]):
        if path_components:
            child_slug = path_components[0]
            remaining_components = path_components[1:]

            try:
                subpage = current_page.get_children().get(slug=child_slug)
            except Page.DoesNotExist:
                return None

            return self.find_page_from_url(subpage, remaining_components)

        else:
            return current_page

    def import_redirect(self, path, redirect_to):
        path_normalised = Redirect.normalise_path(path)

        # Get redirect object
        redirect_object, created = Redirect.objects.get_or_create(old_path=path_normalised)
        redirect_object.site = self.site

        # Add link
        page = self.find_page_from_url(self.site.root_page, [component for component in redirect_to.split('/') if component])
        if page:
            redirect_object.redirect_page = page
        else:
            print "WARN: Cannot find page for: " + redirect_to
            redirect_object.redirect_link = redirect_to

        redirect_object.save()

    def run(self, redirects_dict):
        for redirect in redirects_dict.items():
            self.import_redirect(redirect[0], redirect[1])


def run():
    # Create a new importer
    importer = RedirectsImporter()

    # Run importer
    importer.run(REDIRECTS)
