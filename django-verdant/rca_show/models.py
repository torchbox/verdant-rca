from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models
from django.db.models.functions import Concat
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import RegexURLResolver, Resolver404
from django.conf.urls import url

from modelcluster.fields import ParentalKey

from wagtail.wagtailcore.models import Page, Orderable, Site
from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel, PageChooserPanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailcore.url_routing import RouteResult

from rca.utils.models import CarouselItemFields, SocialFields
from rca_show.utils import get_base_show_template
from taxonomy.models import School, Programme

from rca.models import NewStudentPage, CAMPUS_CHOICES, NewStudentPageQuerySet


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


class ShowPageWithYearTemplateMixin(object):
    """
    A page mixin that allows to customise show templates based on the current year.

    It allows two levels of customisation:

        * It's possible to override a base template to change a logo or an intro video.
          If there is no base template for a specific year, the generic base template is used.

        * You can override a template for a specific page type by appending a year into a template name,
          so `show_exhibition_map_index.html` becomes `show_exhibition_map_index_2016.html`.
          If there is no template for a specific year, generic template for a page type is used
          (e.g. if there is no `show_exhibition_map_index_2016.html`, it uses `show_exhibition_map_index.html`)
    """

    def get_context(self, request, *args, **kwargs):
        context = super(ShowPageWithYearTemplateMixin, self).get_context(request, *args, **kwargs)
        context.update({
            'base_template': get_base_show_template(self.show_index.year),
        })

        return context

    def get_template(self, request, *args, **kwargs):
        if request.is_ajax():
            orig_template = self.ajax_template or self.template
        else:
            orig_template = self.template

        show_index = self.show_index
        if show_index:
            return [
                orig_template.replace('.html', '_{}.html'.format(show_index.year)),
                orig_template
            ]

        return orig_template


# Stream page (for Fashion show)

class ShowStreamPageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca_show.ShowStreamPage', related_name='carousel_items')


class ShowStreamPage(ShowPageWithYearTemplateMixin, Page, SocialFields):
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

    content_panels = Page.content_panels + [
        InlinePanel('carousel_items', label="Carousel content"),
        FieldPanel('body'),
        ImageChooserPanel('poster_image'),
    ]

    promote_panels = [
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


class ShowStandardPage(ShowPageWithYearTemplateMixin, Page, SocialFields):
    body = RichTextField(blank=True)
    map_coords = models.CharField(max_length=255, blank=True, help_text="Lat lon coordinates for centre of map e.g 51.501533, -0.179284")
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio.")
    listing_intro = models.CharField(max_length=100, help_text='Used only on pages listing news items', blank=True)

    @property
    def show_index(self):
        if not hasattr(self, '_show_index'):
            self._show_index = self.get_ancestors().type(ShowIndexPage).last().specific
        return self._show_index

    content_panels = Page.content_panels + [
        FieldPanel('title', classname="full title"),
        InlinePanel('carousel_items', label="Carousel content"),
        FieldPanel('body'),
        FieldPanel('map_coords'),
        InlinePanel('content_block', label="Content block"),
    ]

    promote_panels = [
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


class ShowExhibitionMapIndex(ShowPageWithYearTemplateMixin, Page, SocialFields):
    @property
    def show_index(self):
        if not hasattr(self, '_show_index'):
            self._show_index = self.get_ancestors().type(ShowIndexPage).last().specific
        return self._show_index

    content_panels = Page.content_panels + [
        InlinePanel('content_block', label="Content block"),
    ]

    promote_panels = [
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


class ShowExhibitionMapPage(ShowPageWithYearTemplateMixin, Page, SocialFields):
    body = RichTextField(blank=True)
    campus = models.CharField(max_length=255, choices=CAMPUS_CHOICES, null=True, blank=True)

    @property
    def show_index(self):
        if not hasattr(self, '_show_index'):
            self._show_index = self.get_ancestors().type(ShowIndexPage).last().specific
        return self._show_index

    content_panels = Page.content_panels + [
        FieldPanel('title', classname="full title"),
        FieldPanel('body'),
        FieldPanel('campus'),
    ]

    promote_panels = [
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
    programme = models.ForeignKey('taxonomy.Programme', verbose_name="Programme", on_delete=models.CASCADE, related_name='+')

    panels = [
        FieldPanel('programme'),
    ]


class ShowIndexProgrammeIntro(Orderable):
    page = ParentalKey('rca_show.ShowIndexPage', related_name='programme_intros')
    programme = models.ForeignKey('taxonomy.Programme', verbose_name="Programme", on_delete=models.CASCADE, related_name='+')
    intro = RichTextField(blank=True)

    panels = [
        FieldPanel('programme'),
        FieldPanel('intro'),
    ]


class ShowIndexPageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca_show.ShowIndexPage', related_name='carousel_items')


class ShowIndexPage(SuperPage, SocialFields):
    """
    To find out how templates work for this page type,
    see the the docstring for the ShowPageWithYearTemplateMixin class.

    This page uses the same approach but for multiple sub-views.
    """

    body = RichTextField(blank=True, help_text="Optional body text. Useful for holding pages prior to Show launch.")
    year = models.CharField(max_length=4, blank=True)
    overlay_intro = RichTextField(blank=True)
    exhibition_date = models.TextField(max_length=255, blank=True)
    parent_show_index = models.ForeignKey('rca_show.ShowIndexPage', null=True, blank=True, on_delete=models.SET_NULL)
    password_prompt = models.CharField(max_length=255, blank=True, help_text="A custom message asking the user to log in, on protected pages")
    hide_animation_videos = models.BooleanField(default=True, help_text="If this box is checked, videos embedded in the carousel will not be displayed on Animation and Visual Communication student profiles")

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
    def local_url(self):
        for (id, root_path, root_url) in Site.get_site_root_paths():
            if self.url_path.startswith(root_path):
                return self.url_path[len(root_path) - 1:]

    def get_programmes(self):
        # This method gets hit quite alot (sometimes over 100 times per request)
        if not hasattr(self, '_programmes_cache'):
            self._programmes_cache = Programme.objects.filter(id__in=self.programmes.all().values_list('programme_id', flat=True))

        return self._programmes_cache

    @property
    def is_programme_page(self):
        return bool(self.get_programmes())

    def get_students(self, school=None, programme=None):
        students = NewStudentPageQuerySet(NewStudentPage).live()

        params = {
            'in_show': True,
        }

        if self.year:
            params['current'] = True
            params['current_year'] = self.year

        if programme:
            params['programme'] = programme

            ma_students = students.ma(**params)
            mphil_students = students.mphil(**params)
            phd_students = students.phd(**params)
        else:
            if school:
                params['school'] = school

            programmes = self.get_programmes()
            if programmes:
                ma_students = students.none()
                mphil_students = students.none()
                phd_students = students.none()

                for programme in programmes:
                    params['programme'] = programme

                    ma_students |= students.ma(**params)
                    mphil_students |= students.mphil(**params)
                    phd_students |= students.phd(**params)
            else:
                ma_students = students.ma(**params)
                mphil_students = students.mphil(**params)
                phd_students = students.phd(**params)

        return (ma_students | mphil_students | phd_students).order_by(Concat('first_name', 'last_name')).distinct()

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
            school for school in School.objects.all()
            if self.check_school_has_students(school)
        ]
        school_sort_keys = {
            'schoolofcommunication': 0,
            'schoolofhumanities': 1,
            'schooloffineart': 2,
            'schoolofmaterial': 3,
            'schoolofdesign': 4,
            'schoolofarchitecture': 5,
        }
        schools.sort(key=lambda s: school_sort_keys.get(s.slug))
        return schools

    def get_school_programmes(self, school):
        programmes = [
            programme for programme in school.programmes.all()
            if self.check_programme_has_students(programme)
        ]
        return programmes

    def get_student_url(self, student):
        return self.reverse_subpage(
            'student',
            programme=student.programme,
            slug=student.slug,
        )

    # Views

    def get_context(self, request, *args, **kwargs):
        context = super(ShowIndexPage, self).get_context(request, *args, **kwargs)
        context.update({
            'base_template': get_base_show_template(self.year),
        })

        return context

    def serve_landing(self, request, *args, **kwargs):
        # Render response
        templates = (
            'rca_show/landing_{}.html'.format(self.year),
            'rca_show/landing.html',
        )
        return render(request, templates, self.get_context(request, *args, **kwargs))

    def serve_school_index(self, request, *args, **kwargs):
        # Render response
        templates = (
            'rca_show/school_index_{}.html'.format(self.year),
            'rca_show/school_index.html',
        )
        return render(request, templates, self.get_context(request, *args, **kwargs))

    def serve_school(self, request, school_slug, *args, **kwargs):
        school = get_object_or_404(School, slug=school_slug)
        # Render response
        templates = (
            'rca_show/school+{}.html'.format(self.year),
            'rca_show/school.html',
        )

        context = self.get_context(request, *args, **kwargs)
        context.update({
            'school': school,
        })

        return render(request, templates, context)

    def serve_programme(self, request, programme_slug, school_slug=None, *args, **kwargs):
        programme = get_object_or_404(Programme, slug=programme_slug)

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
            templates = (
                'rca_show/includes/modules/gallery_{}.html'.format(self.year),
                'rca_show/includes/modules/gallery.html',
            )
        else:
            templates = (
                'rca_show/programme_{}.html'.format(self.year),
                'rca_show/programme.html',
            )

        context = self.get_context(request, *args, **kwargs)
        context.update({
            'school': programme.school,
            'programme': programme,
            'intro': intro,
            'students': students
        })

        # Render response
        return render(request, templates, context)

    def serve_student(self, request, programme_slug, slug, school_slug=None, *args, **kwargs):
        programme = get_object_or_404(Programme, slug=programme_slug)

        # Get the student
        try:
            student = self.get_student(programme=programme, slug=slug)
        except NewStudentPage.DoesNotExist:
            raise Http404("Cannot find student")

        # Render response
        return self._serve_student(request, student, *args, **kwargs)

    def _serve_student(self, request, student, *args, **kwargs):
        """
        This part of the student view is separate to allow us to render any student with this shows styling
        This is used for student page previews
        """
        templates = (
            'rca_show/student_{}.html'.format(self.year),
            'rca_show/student.html',
        )

        context = self.get_context(request, *args, **kwargs)
        context.update({
            'school': student.programme.school,
            'programme': student.programme,
            'student': student,
        })
        return render(request, templates, context)

    def serve_preview(self, request, mode_name):
        return self.serve(request, self.serve_landing, [], {})

    def get_subpage_urls(self):
        programme_count = len(self.get_programmes())

        if programme_count == 0:
            return [
                url(r'^$', self.serve_landing, name='landing'),
                url(r'^schools/$', self.serve_school_index, name='school_index'),
                url(r'^(?P<school_slug>[\w\-]+)/$', self.serve_school, name='school'),
                url(r'^(?P<school_slug>[\w\-]+)/(?P<programme_slug>[\w\-]+)/$', self.serve_programme, name='programme'),
                url(r'^(?P<school_slug>[\w\-]+)/(?P<programme_slug>[\w\-]+)/(?P<slug>[\w\-]+)/$', self.serve_student, name='student'),
            ]
        elif programme_count == 1:
            programme = self.programmes.all()[0].programme

            return [
                url(r'^$', self.serve_programme, dict(programme_slug=programme.slug), name='programme'),
                url(r'^(?P<slug>[\w\-]+)/$', self.serve_student, dict(programme_slug=programme.slug), name='student'),
            ]
        else:
            return [
                url(r'^$', self.serve_landing, name='landing'),
                url(r'^(?P<programme_slug>[\w\-]+)/$', self.serve_programme, name='programme'),
                url(r'^(?P<programme_slug>[\w\-]+)/(?P<slug>.+)/$', self.serve_student, name='student'),
            ]

    content_panels = Page.content_panels + [
        FieldPanel('year'),
        FieldPanel('exhibition_date'),
        FieldPanel('body'),
        InlinePanel('carousel_items', label="Carousel content"),
        FieldPanel('overlay_intro'),
        InlinePanel('programme_intros', label="Programme intros"),
        InlinePanel('programmes', label="Programmes"),
        PageChooserPanel('parent_show_index'),
        FieldPanel('password_prompt'),
        FieldPanel('hide_animation_videos'),
    ]

    promote_panels = [
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
