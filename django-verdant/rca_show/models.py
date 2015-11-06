from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.db import models
from django.http import Http404
from django.shortcuts import render, redirect
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import RegexURLResolver, Resolver404
from django.conf.urls import url
from modelcluster.fields import ParentalKey
from wagtail.wagtailcore.models import Page, Orderable, Site
from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel, PageChooserPanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailcore.url_routing import RouteResult
from rca.models import NewStudentPage, SocialFields, CarouselItemFields, SCHOOL_CHOICES, PROGRAMME_CHOICES, SCHOOL_PROGRAMME_MAP, CAMPUS_CHOICES
from rca import utils as rca_utils


class SuperPage(Page):
    """
    This class extends Page by adding methods to allow urlconfs to be embedded inside pages
    """

    def get_subpage_urls(self):
        """
        Override this method to add your own subpage urls
        """
        return []

    def reverse_subpage(self, name, *args, **kwargs):
        """
        This method does the same job as Djangos' built in "urlresolvers.reverse()" function for subpage urlconfs.
        """
        resolver = RegexURLResolver(r'^', self.get_subpage_urls())
        return self.url + resolver.reverse(name, *args, **kwargs)

    def resolve_subpage(self, path):
        """
        This finds a view method/function from a URL path.
        """
        resolver = RegexURLResolver(r'^', self.get_subpage_urls())
        return resolver.resolve(path)

    def route(self, request, path_components):
        """
        This hooks the subpage urls into Wagtails routing.
        """
        try:
            route_result = super(SuperPage, self).route(request, path_components)

            # Don't allow supers route method to serve this page
            if route_result.page == self:
                raise Http404

            return route_result
        except Http404 as e:
            if self.live:
                try:
                    path = '/'.join(path_components)
                    if path:
                        path += '/'

                    return RouteResult(self, self.resolve_subpage(path))
                except Resolver404:
                    pass

            # Reraise
            raise e

    def serve(self, request, view, args, kwargs):
        return view(request, *args, **kwargs)

    is_creatable = False

    class Meta:
        abstract = True


# Stream page (for Fashion show)

class ShowStreamPageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca_show.ShowStreamPage', related_name='carousel_items')

class ShowStreamPage(Page, SocialFields):
    body = RichTextField(blank=True)
    poster_image = models.ForeignKey(
        'rca.RcaImage',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    @property
    def show_index(self):
        if not hasattr(self, '_show_index'):
            self._show_index = self.get_ancestors().type(ShowIndexPage).last().specific
        return self._show_index

ShowStreamPage.content_panels = [
    FieldPanel('title', classname="full title"),
    InlinePanel('carousel_items', label="Carousel content"),
    FieldPanel('body'),
    ImageChooserPanel('poster_image'),
]

ShowStreamPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], "Common page configuration"),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('search_description'),
    ], "Cross-page behaviour"),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], "Social networks"),
]


# Standard page for contacts etc

class ShowStandardPageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca_show.ShowStandardPage', related_name='carousel_items')

class ShowStandardPageContent(Orderable):
    page = ParentalKey('rca_show.ShowStandardPage', related_name='content_block')
    body = RichTextField(blank=True)
    map_coords = models.CharField(max_length=255, blank=True, help_text="Lat lon coordinates for centre of map e.g 51.501533, -0.179284")

    panels = [
        FieldPanel('body'),
        FieldPanel('map_coords')
    ]

class ShowStandardPage(Page, SocialFields):
    body = RichTextField(blank=True)
    map_coords = models.CharField(max_length=255, blank=True, help_text="Lat lon coordinates for centre of map e.g 51.501533, -0.179284")
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio.")
    listing_intro = models.CharField(max_length=100, help_text='Used only on pages listing news items', blank=True)

    @property
    def show_index(self):
        if not hasattr(self, '_show_index'):
            self._show_index = self.get_ancestors().type(ShowIndexPage).last().specific
        return self._show_index

ShowStandardPage.content_panels = [
    FieldPanel('title', classname="full title"),
    InlinePanel('carousel_items', label="Carousel content"),
    FieldPanel('body'),
    FieldPanel('map_coords'),
    InlinePanel('content_block', label="Content block"),
]

ShowStandardPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], "Common page configuration"),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('search_description'),
        FieldPanel('listing_intro'),
        ImageChooserPanel('feed_image'),
    ], "Cross-page behaviour"),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], "Social networks"),
]

class ShowExhibitionMapIndexContent(Orderable):
    page = ParentalKey('rca_show.ShowExhibitionMapIndex', related_name='content_block')
    body = RichTextField(blank=True)
    map_coords = models.CharField(max_length=255, blank=True, help_text="Lat lon coordinates for centre of map e.g 51.501533, -0.179284")

    panels = [
        FieldPanel('body'),
        FieldPanel('map_coords')
    ]

class ShowExhibitionMapIndex(Page, SocialFields):
    @property
    def show_index(self):
        if not hasattr(self, '_show_index'):
            self._show_index = self.get_ancestors().type(ShowIndexPage).last().specific
        return self._show_index

ShowExhibitionMapIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    InlinePanel('content_block', label="Content block"),
]

ShowExhibitionMapIndex.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], "Common page configuration"),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('search_description'),
    ], "Cross-page behaviour"),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], "Social networks"),
]


class ShowExhibitionMapPage(Page, SocialFields):
    body = RichTextField(blank=True)
    campus = models.CharField(max_length=255, choices=CAMPUS_CHOICES, null=True, blank=True)

    @property
    def show_index(self):
        if not hasattr(self, '_show_index'):
            self._show_index = self.get_ancestors().type(ShowIndexPage).last().specific
        return self._show_index

ShowExhibitionMapPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('body'),
    FieldPanel('campus'),
]

ShowExhibitionMapPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], "Common page configuration"),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('search_description'),
    ], "Cross-page behaviour"),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], "Social networks"),
]

# Main show index page (which performs school, programme and student layouts)

class ShowIndexPageProgramme(Orderable):
    page = ParentalKey('rca_show.ShowIndexPage', related_name='programmes')
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES)

    panels = [FieldPanel('programme')]

class ShowIndexProgrammeIntro(Orderable):
    page = ParentalKey('rca_show.ShowIndexPage', related_name='programme_intros')
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES)
    intro = RichTextField(blank=True)

    panels = [FieldPanel('programme'), FieldPanel('intro')]

class ShowIndexPageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca_show.ShowIndexPage', related_name='carousel_items')

class ShowIndexPage(SuperPage, SocialFields):
    body = RichTextField(blank=True, help_text="Optional body text. Useful for holding pages prior to Show launch.")
    year = models.CharField(max_length=4, blank=True)
    overlay_intro = RichTextField(blank=True)
    exhibition_date = models.TextField(max_length=255, blank=True)
    parent_show_index = models.ForeignKey('rca_show.ShowIndexPage', null=True, blank=True, on_delete=models.SET_NULL)
    password_prompt = models.CharField(max_length=255, blank=True, help_text="A custom message asking the user to log in, on protected pages")

    password_required_template = "rca_show/login.html"

    @property
    def show_index(self):
        return self

    @property
    def menu_items(self):
        menu_items = []

        # Get show index for the menu
        show_index = self.parent_show_index or self

        # Schools & Programmes link
        if len(show_index.get_programmes()) == 0:
            if self.get_schools() and self.get_students():
                menu_items.append(
                    (show_index.reverse_subpage('school_index'), "Schools & Students"),
                )

        # Links to show index subpages
        menu_items.extend([
            (page.url, page.title) for page in show_index.get_children().live().filter(show_in_menus=True)
        ])

        return menu_items

    @property
    def school(self):
        return rca_utils.get_school_for_programme(self.programme)

    @property
    def local_url(self):
        root_paths = Site.get_site_root_paths()
        for (id, root_path, root_url) in Site.get_site_root_paths():
            if self.url_path.startswith(root_path):
                return self.url_path[len(root_path) - 1:]

    def get_programmes(self):
        # This method gets hit quite alot (sometimes over 100 times per request)
        if not hasattr(self, '_programmes_cache'):
            self._programmes_cache = self.programmes.all().values_list('programme', flat=True)

        return self._programmes_cache

    @property
    def is_programme_page(self):
        return bool(self.get_programmes())

    def get_students(self, school=None, programme=None, orderby="first_name"):
        q = models.Q(in_show=True)

        if self.year:
            q &= models.Q(graduation_year=self.year)

        if school:
            q &= models.Q(school=school)

        if programme:
            q &= models.Q(programme=programme)
        else:
            programmes = self.get_programmes()
            if programmes:
                q &= models.Q(programme__in=programmes)

        # If this is the 2015 visual communication show, make that the first carousel item is an embed
        if self.year == '2015' and 'visualcommunication' in self.get_programmes():
            q &= models.Q(carousel_items__sort_order=0) & models.Q(carousel_items__embedly_url__startswith='http')

        return rca_utils.get_students(degree_q=q).order_by(orderby).distinct()

    def get_rand_students(self, school=None, programme=None):
        return self.get_students(school, programme).order_by('random_order')[:20]

    def get_student(self, school=None, programme=None, slug=None):
        return self.get_students(school, programme).get(slug=slug)

    def check_school_has_students(self, school):
        return self.get_students(school=school).exists()

    def check_programme_has_students(self, programme):
        return self.get_students(programme=programme).exists()

    def get_schools(self):
        schools = [
            school for school in rca_utils.get_schools(year=self.year)
            if self.check_school_has_students(school)
        ]
        schools.sort()
        return schools

    def get_school_programmes(self, school):
        programmes = [
            programme for programme in rca_utils.get_programmes(school, year=self.year)
            if self.check_programme_has_students(programme)
        ]
        programmes.sort()
        return programmes

    def get_student_url(self, student):
        return self.reverse_subpage(
            'student',
            programme=student.programme,
            slug=student.slug,
        )

    def contains_school(self, school):
        if self.is_programme_page:
            return False

        if len(rca_utils.get_programmes(school, year=self.year)) == 0:
            return False

        return self.check_school_has_students(school)

    def contains_programme(self, programme):
        programmes = self.get_programmes() or rca_utils.get_programmes(year=self.year)

        if not programme in programmes:
            return False

        return self.check_programme_has_students(programme)

    # Views
    landing_template = 'rca_show/landing.html'
    school_index_template = 'rca_show/school_index.html'
    school_template = 'rca_show/school.html'
    programme_template = 'rca_show/programme.html'
    student_template = 'rca_show/student.html'

    def serve_landing(self, request):
        # Render response
        return render(request, self.landing_template, {
            'self': self,
        })

    def serve_school_index(self, request):
        # Render response
        return render(request, self.school_index_template, {
            'self': self,
        })

    def serve_school(self, request, school):
        # Check that the school exists
        if not self.contains_school(school):
            raise Http404("School doesn't exist")

        # Render response
        return render(request, self.school_template, {
            'self': self,
            'school': school,
        })

    def serve_programme(self, request, programme, school=None):
        # Check that the programme exists
        if not self.contains_programme(programme):
            raise Http404("Programme doesn't exist")

        # Get programme intro
        try:
            intro = self.programme_intros.get(programme=programme).intro
        except ShowIndexProgrammeIntro.DoesNotExist:
            intro = ''

        # Pagination
        page = request.GET.get('page')
        paginator = Paginator(self.get_students(
            programme=programme
        ), 6)
        try:
            students = paginator.page(page)
        except PageNotAnInteger:
            students = paginator.page(1)
        except EmptyPage:
            students = paginator.page(paginator.num_pages)

        # Get template
        if request.is_ajax() and 'pjax' not in request.GET:
            template = 'rca_show/includes/modules/gallery.html'
        else:
            template = self.programme_template

        # Render response
        return render(request, template, {
            'self': self,
            'school': rca_utils.get_school_for_programme(programme, year=self.year),
            'programme': programme,
            'intro': intro,
            'students': students
        })

    def serve_student(self, request, programme, slug, school=None):
        # Check that the programme exists
        if not self.contains_programme(programme):
            raise Http404("Programme doesn't exist")

        # Get the student
        try:
            student = self.get_student(programme=programme, slug=slug)
        except NewStudentPage.DoesNotExist:
            raise Http404("Cannot find student")

        # Render response
        return self._serve_student(request, student)

    def _serve_student(self, request, student):
        """
        This part of the student view is separate to allow us to render any student with this shows styling
        This is used for student page previews
        """
        return render(request, self.student_template, {
            'self': self,
            'school': rca_utils.get_school_for_programme(student.programme, year=self.year),
            'programme': student.programme,
            'student': student,
        })

    def serve_preview(self, request, mode_name):
        return self.serve(request, self.serve_landing, [], {})

    def get_subpage_urls(self):
        programme_count = len(self.get_programmes())

        if programme_count == 0:
            return [
                url(r'^$', self.serve_landing, name='landing'),
                url(r'^schools/$', self.serve_school_index, name='school_index'),
                url(r'^(?P<school>[\w\-]+)/$', self.serve_school, name='school'),
                url(r'^(?P<school>[\w\-]+)/(?P<programme>[\w\-]+)/$', self.serve_programme, name='programme'),
                url(r'^(?P<school>[\w\-]+)/(?P<programme>[\w\-]+)/(?P<slug>[\w\-]+)/$', self.serve_student, name='student'),
            ]
        elif programme_count == 1:
            programme = self.programmes.all()[0].programme

            return [
                url(r'^$', self.serve_programme, dict(programme=programme, school=None), name='programme'),
                url(r'^(?P<slug>[\w\-]+)/$', self.serve_student, dict(programme=programme, school=None), name='student'),
            ]
        else:
            return [
                url(r'^$', self.serve_landing, name='landing'),
                url(r'^(?P<programme>[\w\-]+)/$', self.serve_programme, dict(school=None), name='programme'),
                url(r'^(?P<programme>[\w\-]+)/(?P<slug>.+)/$', self.serve_student, dict(school=None), name='student'),
            ]

ShowIndexPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('year'),
    FieldPanel('exhibition_date'),
    FieldPanel('body'),
    InlinePanel('carousel_items', label="Carousel content"),
    FieldPanel('overlay_intro'),
    InlinePanel('programme_intros', label="Programme intros"),
    InlinePanel('programmes', label="Programmes"),
    PageChooserPanel('parent_show_index'),
    FieldPanel('password_prompt'),
]

ShowIndexPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], "Common page configuration"),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('search_description'),
    ], "Cross-page behaviour"),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], "Social networks"),
]
