from django.db import models, connection
from django.db.models import get_model
from django.http import Http404
from django.shortcuts import render

from django.contrib.contenttypes.models import ContentType
from treebeard.mp_tree import MP_Node

from core.util import camelcase_to_underscore


# We try to do database access on app startup (namely, looking up content types) -
# which will fail if the db hasn't been initialised (e.g. when running the initial syncdb).
# So, need to explicitly test whether the database is usable yet. (Ugh.)
DB_IS_READY = ('django_content_type' in connection.introspection.table_names())


class SiteManager(models.Manager):
    def get_by_natural_key(self, hostname):
        return self.get(hostname=hostname)


class Site(models.Model):
    hostname = models.CharField(max_length=255, unique=True, db_index=True)
    root_page = models.ForeignKey('Page', related_name='sites_rooted_here')

    def natural_key(self):
        return (self.hostname,)

    def __unicode__(self):
        if self.hostname == '*':
            return "[Default site]"
        else:
            return self.hostname


PAGE_CONTENT_TYPES = []
def get_page_types():
    return PAGE_CONTENT_TYPES

LEAF_PAGE_CONTENT_TYPE_IDS = []
NAVIGABLE_PAGE_CONTENT_TYPE_IDS = []

class PageBase(models.base.ModelBase):
    """Metaclass for Page"""
    def __init__(cls, name, bases, dct):
        super(PageBase, cls).__init__(name, bases, dct)
        if 'template' not in dct:
            # Define a default template path derived from the app name and model name
            cls.template = "%s/%s.html" % (cls._meta.app_label, camelcase_to_underscore(name))

        cls._clean_subpage_types = None  # to be filled in on first call to cls.clean_subpage_types

        if not dct.get('is_abstract'):
            # subclasses are only abstract if the subclass itself defines itself so
            cls.is_abstract = False

        if DB_IS_READY:
            if not cls.is_abstract:
                # register this type in the list of page content types
                PAGE_CONTENT_TYPES.append(ContentType.objects.get_for_model(cls))
            if cls.subpage_types:
                NAVIGABLE_PAGE_CONTENT_TYPE_IDS.append(
                    ContentType.objects.get_for_model(cls).id)
            else:
                LEAF_PAGE_CONTENT_TYPE_IDS.append(
                    ContentType.objects.get_for_model(cls).id)


class Page(MP_Node):
    __metaclass__ = PageBase

    title = models.CharField(max_length=255, help_text="The page title as you'd like it to be seen by the public")
    slug = models.SlugField()
    # TODO: enforce uniqueness on slug field per parent (will have to be done at the Django
    # level rather than db, since there is no explicit parent relation in the db)
    content_type = models.ForeignKey('contenttypes.ContentType', related_name='pages')

    def __init__(self, *args, **kwargs):
        super(Page, self).__init__(*args, **kwargs)
        if not self.content_type_id:
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
            return self.serve(request)

    def serve(self, request):
        return render(request, self.template, {
            'self': self
        })

    def is_navigable(self):
        """
        Return true if it's meaningful to browse subpages of this page -
        i.e. it currently has subpages, or its page type indicates that sub-pages are supported
        """
        return (not self.is_leaf()) or (self.content_type_id not in LEAF_PAGE_CONTENT_TYPE_IDS)

    @property
    def url(self):
        paths = [
            self.path[0:pos]
            for pos in range(0, len(self.path) + self.steplen, self.steplen)[1:]
        ]
        ancestors = Page.objects.filter(path__in=paths).order_by('-depth').prefetch_related('sites_rooted_here')
        path_components = []

        site = None
        for ancestor in ancestors:
            sites_rooted_here = ancestor.sites_rooted_here.all()
            if sites_rooted_here:
                site = sites_rooted_here[0]
                break
            else:
                path_components.insert(0, ancestor.slug)

        # FIXME: support cross-domain links
        return '/' + '/'.join(path_components) + '/'


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


def get_navigation_menu_items():
    # Get all pages that appear in the navigation menu: ones which have children,
    # or are a non-leaf type (indicating that they *could* have children)
    if NAVIGABLE_PAGE_CONTENT_TYPE_IDS:
        pages = Page.objects.raw("""
            SELECT * FROM core_page
            WHERE numchild > 0 OR content_type_id IN %s
            ORDER BY path
        """, [tuple(NAVIGABLE_PAGE_CONTENT_TYPE_IDS)])
    else:
        pages = Page.objects.raw("""
            SELECT * FROM core_page
            WHERE numchild > 0
            ORDER BY path
        """)

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
