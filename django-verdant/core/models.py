from django.db import models
from django.db.models import get_model
from django.http import Http404
from django.shortcuts import render

from django.contrib.contenttypes.models import ContentType
from treebeard.mp_tree import MP_Node
from cluster.models import ClusterableModel

from core.util import camelcase_to_underscore


class SiteManager(models.Manager):
    def get_by_natural_key(self, hostname):
        return self.get(hostname=hostname)


class Site(models.Model):
    hostname = models.CharField(max_length=255, unique=True, db_index=True)
    port = models.IntegerField(default=80, help_text="Set this to something other than 80 if you need a specific port number to appear in URLs (e.g. development on port 8000). Does not affect request handling (so port forwarding still works).")
    root_page = models.ForeignKey('Page', related_name='sites_rooted_here')
    is_default_site = models.BooleanField(default=False, help_text="If true, this site will handle requests for all other hostnames that do not have a site entry of their own")

    def natural_key(self):
        return (self.hostname,)

    def __unicode__(self):
        return self.hostname + ("" if self.port == 80 else (":%d" % self.port)) + (" [default]" if self.is_default_site else "")

    @staticmethod
    def find_for_request(request):
        """Find the site object responsible for responding to this HTTP request object"""
        hostname = request.META['HTTP_HOST'].split(':')[0]
        try:
            # find a Site matching this specific hostname
            return Site.objects.get(hostname=hostname)
        except Site.DoesNotExist:
            # failing that, look for a catch-all Site. If that fails, let the Site.DoesNotExist propagate back to the caller
            return Site.objects.get(is_default_site=True)


PAGE_MODEL_CLASSES = []
_PAGE_CONTENT_TYPES = []
def get_page_types():
    global _PAGE_CONTENT_TYPES
    if len(_PAGE_CONTENT_TYPES) != len(PAGE_MODEL_CLASSES):
        _PAGE_CONTENT_TYPES = [
            ContentType.objects.get_for_model(cls) for cls in PAGE_MODEL_CLASSES
        ]
    return _PAGE_CONTENT_TYPES

LEAF_PAGE_MODEL_CLASSES = []
_LEAF_PAGE_CONTENT_TYPE_IDS = []
def get_leaf_page_content_type_ids():
    global _LEAF_PAGE_CONTENT_TYPE_IDS
    if len(_LEAF_PAGE_CONTENT_TYPE_IDS) != len(LEAF_PAGE_MODEL_CLASSES):
        _LEAF_PAGE_CONTENT_TYPE_IDS = [
            ContentType.objects.get_for_model(cls).id for cls in LEAF_PAGE_MODEL_CLASSES
        ]
    return _LEAF_PAGE_CONTENT_TYPE_IDS

NAVIGABLE_PAGE_MODEL_CLASSES = []
_NAVIGABLE_PAGE_CONTENT_TYPE_IDS = []
def get_navigable_page_content_type_ids():
    global _NAVIGABLE_PAGE_CONTENT_TYPE_IDS
    if len(_NAVIGABLE_PAGE_CONTENT_TYPE_IDS) != len(NAVIGABLE_PAGE_MODEL_CLASSES):
        _NAVIGABLE_PAGE_CONTENT_TYPE_IDS = [
            ContentType.objects.get_for_model(cls).id for cls in NAVIGABLE_PAGE_MODEL_CLASSES
        ]
    return _NAVIGABLE_PAGE_CONTENT_TYPE_IDS

class PageBase(models.base.ModelBase):
    """Metaclass for Page"""
    def __init__(cls, name, bases, dct):
        super(PageBase, cls).__init__(name, bases, dct)

        if cls._deferred:
            # this is an internal class built for Django's deferred-attribute mechanism;
            # don't proceed with all this page type registration stuff
            return

        if 'template' not in dct:
            # Define a default template path derived from the app name and model name
            cls.template = "%s/%s.html" % (cls._meta.app_label, camelcase_to_underscore(name))

        cls._clean_subpage_types = None  # to be filled in on first call to cls.clean_subpage_types

        if not dct.get('is_abstract'):
            # subclasses are only abstract if the subclass itself defines itself so
            cls.is_abstract = False

        if not cls.is_abstract:
            # register this type in the list of page content types
            PAGE_MODEL_CLASSES.append(cls)
        if cls.subpage_types:
            NAVIGABLE_PAGE_MODEL_CLASSES.append(cls)
        else:
            LEAF_PAGE_MODEL_CLASSES.append(cls)


class Page(MP_Node, ClusterableModel):
    __metaclass__ = PageBase

    title = models.CharField(max_length=255, help_text="The page title as you'd like it to be seen by the public")
    slug = models.SlugField()
    # TODO: enforce uniqueness on slug field per parent (will have to be done at the Django
    # level rather than db, since there is no explicit parent relation in the db)
    content_type = models.ForeignKey('contenttypes.ContentType', related_name='pages')
    live = models.BooleanField(default=True, editable=False)
    has_unpublished_changes = models.BooleanField(default=False, editable=False)

    # RCA-specific fields
    # TODO: decide on the best way of implementing site-specific but site-global fields,
    # and decide which (if any) of these are more generally useful and should be kept in Verdant core
    seo_title = models.CharField("Page title", max_length=255, blank=True, help_text="Optional. 'Search Engine Friendly' title. This will appear at the top of the browser window.")
    show_in_menus = models.BooleanField(default=False, help_text="Whether a link to this page will appear in automatically generated menus")
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+', help_text="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio.")
    # End RCA-specific fields

    def __init__(self, *args, **kwargs):
        super(Page, self).__init__(*args, **kwargs)
        if not self.id and not self.content_type_id:
            # this model is being newly created rather than retrieved from the db;
            # set content type to correctly represent the model class that this was
            # created as
            self.content_type = ContentType.objects.get_for_model(self)

    def __unicode__(self):
        return self.title

    # by default pages do not allow any kind of subpages
    subpage_types = []

    is_abstract = True  # don't offer Page in the list of page types a superuser can create

    @property
    def specific(self):
        """
            Return this page in its most specific subclassed form.
        """
        # the ContentType.objects manager keeps a cache, so this should potentially
        # avoid a database lookup over doing self.content_type. I think.
        content_type = ContentType.objects.get_for_id(self.content_type_id)
        if isinstance(self, content_type.model_class()):
            # self is already the an instance of the most specific class
            return self
        else:
            return content_type.get_object_for_this_type(id=self.id)

    @property
    def specific_class(self):
        """
            return the class that this page would be if instantiated in its
            most specific form
        """
        content_type = ContentType.objects.get_for_id(self.content_type_id)
        return content_type.model_class()

    def route(self, request, path_components):
        if path_components:
            # request is for a child of this page
            child_slug = path_components[0]
            remaining_components = path_components[1:]

            try:
                subpage = self.get_children().get(slug=child_slug)
            except Page.DoesNotExist:
                raise Http404

            return subpage.specific.route(request, remaining_components)

        else:
            # request is for this very page
            if self.live:
                return self.serve(request)
            else:
                raise Http404

    def save_revision(self):
        self.revisions.create(content_json=self.to_json())

    def get_latest_revision(self):
        try:
            revision = self.revisions.order_by('-created_at')[0]
        except IndexError:
            return self.specific

        result = self.specific_class.from_json(revision.content_json)

        # Override the possibly-outdated tree parameter fields from the revision object
        # with up-to-date values
        result.path = self.path
        result.depth = self.depth
        result.numchild = self.numchild

        return result

    def serve(self, request):
        return render(request, self.template, {
            'self': self
        })

    def is_navigable(self):
        """
        Return true if it's meaningful to browse subpages of this page -
        i.e. it currently has subpages, or its page type indicates that sub-pages are supported,
        or it's at the top level (this rule necessary for empty out-of-the-box sites to have working navigation)
        """
        return (not self.is_leaf()) or (self.content_type_id not in get_leaf_page_content_type_ids()) or self.depth == 2

    def get_other_siblings(self):
        # get sibling pages excluding self
        return self.get_siblings().exclude(id=self.id)

    @property
    def url(self):
        if not hasattr(self, '_url_base'):
            self._set_url_properties()
        if self._url_base:
            return self._url_base + self._url_path

    def relative_url(self, current_site):
        if not hasattr(self, '_url_base'):
            self._set_url_properties()
        if self._url_site_id == current_site.id:
            # don't prepend the full _url_base, just add a slash
            return '/' + self._url_path
        else:
            return self._url_base + self._url_path

    def _set_url_properties(self):
        # populate a bunch of properties necessary for forming relative URLs:
        # _url_path - the path portion of the url (without the initial '/')
        # _url_site_id - the site
        # _url_base - the http://example.com:8000/ portion of the url

        # get a list of all ancestor paths of this page
        paths = [
            self.path[0:pos]
            for pos in range(0, len(self.path) + self.steplen, self.steplen)[1:]
        ]
        # retrieve the pages with those paths, along with any site records that they
        # are roots of. We don't worry about the join returning multiple results because
        # 1) we're going to stop at the first row where we see a site, and 2) people really
        # shouldn't be rooting sites at the same place anyway.
        pages = Page.objects.raw("""
            SELECT
                core_page.id, core_page.slug,
                core_site.id AS site_id, core_site.hostname, core_site.port
            FROM
                core_page
                LEFT JOIN core_site ON (core_page.id = core_site.root_page_id)
            WHERE
                core_page.path IN %s
            ORDER BY
                core_page.depth DESC
        """, [tuple(paths)])

        url = ''
        for page in pages:
            if page.site_id:
                # we've found a site root
                self._url_site_id = page.site_id
                self._url_path = url
                if page.port == 80:
                    self._url_base = "http://%s/" % page.hostname
                else:
                    self._url_base = "http://%s:%d/" % (page.hostname, page.port)
                return
            else:
                # attach the parent's slug and move on to the next level up
                url = page.slug + '/' + url

        # if we got here, we've reached the end of the ancestor list without finding a site,
        # which means that this page doesn't have a routeable URL
        self._url_site_id = None
        self._url_path = None
        self._url_base = None

    @classmethod
    def clean_subpage_types(cls):
        """
            Returns the list of subpage types, with strings converted to class objects
            where required
        """
        if cls._clean_subpage_types is None:
            res = []
            for page_type in cls.subpage_types:
                if isinstance(page_type, basestring):
                    try:
                        app_label, model_name = page_type.split(".")
                    except ValueError:
                        # If we can't split, assume a model in current app
                        app_label = cls._meta.app_label
                        model_name = page_type

                    model = get_model(app_label, model_name)
                    if model:
                        res.append(model)
                    else:
                        raise NameError("name '%s' (used in subpage_types list) is not defined " % page_type)

                else:
                    # assume it's already a model class
                    res.append(page_type)

            cls._clean_subpage_types = res

        return cls._clean_subpage_types

    @classmethod
    def allowed_parent_page_types(cls):
        """
            Returns the list of page types that this page type can be a subpage of
        """
        return [ct for ct in get_page_types() if cls in ct.model_class().clean_subpage_types()]

    @classmethod
    def allowed_parent_pages(cls):
        """
            Returns the list of pages that this page type can be a subpage of
        """
        return Page.objects.filter(content_type__in=cls.allowed_parent_page_types())

    @property
    def status_string(self):
        if not self.live:
            return "draft"
        else:
            if self.has_unpublished_changes:
                return "live with draft updates"
            else:
                return "live"


def get_navigation_menu_items(depth=2):
    # Get all pages that appear in the navigation menu: ones which have children,
    # or are a non-leaf type (indicating that they *could* have children),
    # or are at the top-level (this rule required so that an empty site out-of-the-box has a working menu)
    navigable_content_type_ids = get_navigable_page_content_type_ids()
    if navigable_content_type_ids:
        pages = Page.objects.raw("""
            SELECT * FROM core_page
            WHERE numchild > 0 OR content_type_id IN %s OR depth = %s
            ORDER BY path
        """, [tuple(navigable_content_type_ids), depth])
    else:
        pages = Page.objects.raw("""
            SELECT * FROM core_page
            WHERE numchild > 0 OR depth = %s
            ORDER BY path
        """, [depth])

    # Turn this into a tree structure:
    #     tree_node = (page, children)
    #     where 'children' is a list of tree_nodes.
    # Algorithm:
    # Maintain a list that tells us, for each depth level, the last page we saw at that depth level.
    # Since our page list is ordered by path, we know that whenever we see a page
    # at depth d, its parent must be the last page we saw at depth (d-1), and so we can
    # find it in that list.

    depth_list = [(None, [])]  # a dummy node for depth=0, since one doesn't exist in the DB

    for page in pages:
        # create a node for this page
        node = (page, [])
        # retrieve the parent from depth_list
        parent_page, parent_childlist = depth_list[page.depth - 1]
        # insert this new node in the parent's child list
        parent_childlist.append(node)

        # add the new node to depth_list
        try:
            depth_list[page.depth] = node
        except IndexError:
            # an exception here means that this node is one level deeper than any we've seen so far
            depth_list.append(node)

    # in Verdant, the convention is to have one root node in the db (depth=1); the menu proper
    # begins with the children of that node (depth=2).
    try:
        root, root_children = depth_list[1]
        return root_children
    except IndexError:
        # what, we don't even have a root node? Fine, just return an empty list...
        []


class Orderable(models.Model):
    sort_order = models.IntegerField(null=True, blank=True, editable=False)
    sort_order_field = 'sort_order'

    class Meta:
        abstract = True
        ordering = ['sort_order']


class PageRevision(models.Model):
    page = models.ForeignKey('Page', related_name='revisions')
    created_at = models.DateTimeField(auto_now_add=True)
    content_json = models.TextField()
