from django.conf import settings
from django.db import models
from django.http import Http404
from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import RegexURLResolver
from django.conf.urls import url
from modelcluster.fields import ParentalKey
from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailcore.fields import RichTextField
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
        return [
            url('^$', self.serve, name='main'),
        ]

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
        if self.live:
            try:
                path = '/'.join(path_components)
                if path:
                    path += '/'

                view, args, kwargs = self.resolve_subpage(path)
                return view(request, *args, **kwargs)
            except Http404:
                pass

        return super(SuperPage, self).route(request, path_components)

    is_abstract = True

    class Meta:
        abstract = True


# Stream page (for Fashion show)

class ShowStreamPageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca_show.ShowStreamPage', related_name='carousel_items')

class ShowStreamPage(Page, SocialFields):
    body = RichTextField(blank=True)

    def get_show_index(self):
        for page in self.get_ancestors().reverse():
            specific_page = page.specific
            if isinstance(specific_page, ShowIndexPage):
                return specific_page

ShowStreamPage.content_panels = [
    FieldPanel('title', classname="full title"),
    InlinePanel(ShowStreamPage, 'carousel_items', label="Carousel content"),
    FieldPanel('body'),
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

    def get_show_index(self):
        for page in self.get_ancestors().reverse():
            specific_page = page.specific
            if isinstance(specific_page, ShowIndexPage):
                return specific_page

ShowStandardPage.content_panels = [
    FieldPanel('title', classname="full title"),
    InlinePanel(ShowStandardPage, 'carousel_items', label="Carousel content"),
    FieldPanel('body'),
    FieldPanel('map_coords'),
    InlinePanel(ShowStandardPage, 'content_block', label="Content block"),
]

ShowStandardPage.promote_panels = [
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

class ShowExhibitionMapIndexContent(Orderable):
    page = ParentalKey('rca_show.ShowExhibitionMapIndex', related_name='content_block')
    body = RichTextField(blank=True)
    map_coords = models.CharField(max_length=255, blank=True, help_text="Lat lon coordinates for centre of map e.g 51.501533, -0.179284")

    panels = [
        FieldPanel('body'), 
        FieldPanel('map_coords')
    ]

class ShowExhibitionMapIndex(Page, SocialFields):
    pass

ShowExhibitionMapIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    InlinePanel(ShowExhibitionMapIndex, 'content_block', label="Content block"),
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

class ShowIndexPageSchool(Orderable):
    page = ParentalKey('rca_show.ShowIndexPage', related_name='schools')
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES)
    intro = RichTextField(blank=True)

    panels = [FieldPanel('school'), FieldPanel('intro')]

class ShowIndexPageProgramme(Orderable):
    page = ParentalKey('rca_show.ShowIndexPage', related_name='programmes')
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES)

    panels = [FieldPanel('programme')]

class ShowIndexPage(SuperPage, SocialFields):
    year = models.CharField(max_length=4, blank=True)
    overlay_intro = RichTextField(blank=True)
    exhibition_date = models.CharField(max_length=255, blank=True)

    @property
    def school(self):
        return rca_utils.get_school_for_programme(self.programme)

    def get_programmes(self):
        # This method gets hit quite alot (sometimes over 100 times per request)
        if not hasattr(self, '_programmes_cache'):
            self._programmes_cache = self.programmes.all().values_list('programme', flat=True)

        return self._programmes_cache

    @property
    def is_programme_page(self):
        return bool(self.get_programmes())

    def get_ma_students_q(self, school=None, programme=None):
        filters = {
            'ma_in_show': True,
        }

        if self.year:
            filters['ma_graduation_year'] = self.year

        programmes = self.get_programmes()
        if programmes:
            filters['ma_programme__in'] = programmes

        if school:
            filters['ma_school'] = school

        if programme:
            filters['ma_programme'] = programme

        return models.Q(**filters)

    def get_mphil_students_q(self, school=None, programme=None):
        filters = {
            'mphil_in_show': True,
        }

        if self.year:
            filters['mphil_graduation_year'] = self.year

        programmes = self.get_programmes()
        if programmes:
            filters['mphil_programme__in'] = programmes

        if school:
            filters['mphil_school'] = school

        if programme:
            filters['mphil_programme'] = programme

        return models.Q(**filters)

    def get_phd_students_q(self, school=None, programme=None):
        filters = {
            'phd_in_show': True,
        }

        if self.year:
            filters['phd_graduation_year'] = self.year

        programmes = self.get_programmes()
        if programmes:
            filters['phd_programme__in'] = programmes

        if school:
            filters['phd_school'] = school

        if programme:
            filters['phd_programme'] = programme

        return models.Q(**filters)

    def get_students(self, school=None, programme=None):
        students = NewStudentPage.objects.filter(live=True)

        # Filter by students in this particular show
        students = students.filter(self.get_ma_students_q(school, programme) | self.get_mphil_students_q(school, programme) | self.get_phd_students_q(school, programme)).order_by('first_name')

        return students

    def get_rand_students(self, school=None, programme=None):
        return self.get_students(school, programme).order_by('random_order')[:20]

    def get_student(self, school=None, programme=None, slug=None):
        return self.get_students(school, programme).get(slug=slug)

    def get_schools(self):
        return [school.school for school in self.schools.all()]

    def get_school_programmes(self, school):
        return rca_utils.get_programmes(school, self.year)

    def get_student_url(self, student):
        return self.reverse_subpage(
            'student',
            programme=student.programme,
            slug=student.slug,
        )

    def contains_programme(self, programme):
        programmes = self.get_programmes() or rca_utils.get_programmes(year=self.year)
        return programme in programmes

    # Views
    landing_template = 'rca_show/landing.html'
    school_index_template = 'rca_show/school_index.html'
    school_template = 'rca_show/school.html'
    programme_template = 'rca_show/programme.html'
    student_template = 'rca_show/student.html'

    def serve(self, request):
        # If serve called directly (eg, from preview) redirect to serve_landing
        return self.serve_landing(request)

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
        if self.get_school_programmes(school) is None:
            raise Http404("School doesn't exist")

        # Get school intro
        try:
            intro = self.schools.get(school=school).intro
        except ShowIndexPageSchool.DoesNotExist:
            intro = ''

        # Render response
        return render(request, self.school_template, {
            'self': self,
            'school': school,
            'intro': intro,
        })

    def serve_programme(self, request, programme, school=None):
        # Check that the programme exists
        if not self.contains_programme(programme):
            raise Http404("Programme doesn't exist")

        # Render response
        return render(request, self.programme_template, {
            'self': self,
            'school': rca_utils.get_school_for_programme(programme, year=self.year),
            'programme': programme,
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
        return render(request, self.student_template, {
            'self': self,
            'school': rca_utils.get_school_for_programme(programme, year=self.year),
            'programme': programme,
            'student': student,
        })

    def get_subpage_urls(self):
        programme_count = self.programmes.count()

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

    def route(self, request, path_components):
        request.show_index = self

        return super(ShowIndexPage, self).route(request, path_components)

ShowIndexPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('year'),
    FieldPanel('exhibition_date'),
    InlinePanel(ShowIndexPage, 'schools', label="Schools"),
    FieldPanel('overlay_intro'),
    InlinePanel(ShowIndexPage, 'programmes', label="Programmes"),
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
