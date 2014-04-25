from django.conf import settings
from django.db import models
from django.http import Http404
from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from modelcluster.fields import ParentalKey
from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailcore.fields import RichTextField
from rca.models import NewStudentPage, SocialFields, CarouselItemFields, SCHOOL_CHOICES, PROGRAMME_CHOICES, SCHOOL_PROGRAMME_MAP

# Standard page for contacts etc

class ShowStandardPageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca_show.ShowStandardPage', related_name='carousel_items')

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

# Main show index page (which performs school, programme and student layouts)

class ShowIndexPageSchool(Orderable):
    page = ParentalKey('rca_show.ShowIndexPage', related_name='schools')
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES)
    intro = RichTextField(blank=True)

    panels = [FieldPanel('school'), FieldPanel('intro')]

class ShowIndexPage(Page, SocialFields):
    year = models.CharField(max_length=4, blank=True)
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True)
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True)
    overlay_intro = RichTextField(blank=True)
    exhibition_date = models.CharField(max_length=255, blank=True)

    def get_ma_students_q(self, school=None, programme=None):
        filters = {
            'ma_in_show': True,
        }

        if self.year:
            filters['ma_graduation_year'] = self.year

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

    def get_student(self, school, programme, slug):
        return self.get_students(school, programme).get(slug=slug)

    def get_schools(self):
        return [school.school for school in self.schools.all()]

    def get_school_programmes(self, school):
        if not self.year in SCHOOL_PROGRAMME_MAP:
            return None

        if not school in SCHOOL_PROGRAMME_MAP[self.year]:
            return None

        return SCHOOL_PROGRAMME_MAP[self.year][school]

    def get_school_index_url(self):
        return self.url + 'schools/'

    def get_school_url(self, school):
        if not self.school:
            return self.url + school + '/'
        else:
            return self.url

    def get_programme_url(self, school, programme):
        if not self.programme:
            return self.get_school_url(school) + programme + '/'
        else:
            return self.get_school_url(school)

    def get_student_url(self, student):
        return self.get_programme_url(student.school, student.programme) + student.slug + '/'

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

    def serve_programme(self, request, school, programme):
        # Check that the school/programme exists
        programmes = self.get_school_programmes(school)
        if programmes is None:
            raise Http404("School doesn't exist")

        if programme not in programmes:
            raise Http404("Programme doesn't exist")

        # Render response
        return render(request, self.programme_template, {
            'self': self,
            'school': school,
            'programme': programme,
        })

    def serve_student(self, request, school, programme, slug):
        # Get the student
        try:
            student = self.get_student(school, programme, slug)
        except NewStudentPage.DoesNotExist:
            raise Http404("Cannot find student")

        # Render response
        return render(request, self.student_template, {
            'self': self,
            'school': school,
            'programme': programme,
            'student': student,
        })

    def route(self, request, path_components):
        request.show_index = self

        if self.live:
            # Check if this is a request for the schools index
            if not self.school and len(path_components) == 1 and path_components[0] == 'schools':
                return self.serve_school_index(request)

            # Check if this is a request for the landing page
            if not self.school and not path_components:
                return self.serve_landing(request)

            # Must be for a school/programme/student find the slugs
            slugs = []
            if self.school:
                slugs.append(self.school)
                if self.programme:
                    slugs.append(self.programme)
            slugs.extend(path_components)

            try:
                if len(slugs) == 1:
                    return self.serve_school(request, slugs[0])
                elif len(slugs) == 2:
                    return self.serve_programme(request, slugs[0], slugs[1])
                elif len(slugs) == 3:
                    return self.serve_student(request, slugs[0], slugs[1], slugs[2])
            except Http404:
                pass

        if path_components:
            # Fallback to subpage
            child_slug = path_components[0]
            remaining_components = path_components[1:]
            try:
                subpage = self.get_children().get(slug=child_slug)
            except Page.DoesNotExist:
                raise Http404

            return subpage.specific.route(request, remaining_components)
        else:
            raise Http404

ShowIndexPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('year'),
    FieldPanel('exhibition_date'),
    InlinePanel(ShowIndexPage, 'schools', label="Schools"),
    MultiFieldPanel([
        FieldPanel('school'),
        FieldPanel('programme'),
        FieldPanel('overlay_intro'),
    ], "Limit page to this school/programme"),
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
