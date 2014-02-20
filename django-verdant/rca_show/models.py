from django.db import models
from django.http import Http404
from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from modelcluster.fields import ParentalKey
from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailcore.fields import RichTextField
from rca.models import StudentPage, SocialFields, SCHOOL_CHOICES


class ShowIndexPageSchool(Orderable):
    page = ParentalKey('rca_show.ShowIndexPage', related_name='schools')
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES)
    intro = RichTextField()

    panels = [FieldPanel('school'), FieldPanel('intro')]

class ShowIndexPage(Page, SocialFields):
    year = models.CharField(max_length=4, blank=True)

    def get_students(self, school=None, programme=None):
        students = StudentPage.objects.filter(live=True, degree_year=self.year)

        if school:
            students = students.filter(school=school)

        if programme:
            students = students.filter(programme=programme)

        return students

    def get_student(self, school, programme, slug):
        return self.get_students(school, programme).get(slug=slug)

    def get_schools(self):
        return [school.school for school in self.schools.all()]

    def get_school_programmes(self, school):
        return [
            values['programme']
            for values in self.get_students(school).order_by('programme').distinct('programme').values('programme')
        ]

    def get_school_index_url(self):
        return self.url + 'schools/'

    def get_school_url(self, school):
        return self.url + school + '/'

    def get_programme_url(self, school, programme):
        return self.get_school_url(school) + programme + '/'

    def get_student_url(self, student):
        return self.get_programme_url(student.school, student.programme) + student.slug + '/'

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
        # Check if school exists
        try:
            school_obj = self.schools.get(school=school)
        except ShowIndexPageSchool.DoesNotExist:
            raise Http404("Cannot find school")

        # Render response
        return render(request, self.school_template, {
            'self': self,
            'school': school,
            'intro': school_obj.intro,
        })

    def serve_programme(self, request, school, programme):
        # Get students for this programme
        students = self.get_students(school, programme)

        # If there are no students, this programme doesn't exist!
        if not students:
            raise Http404("No students exist with this programme")

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
        except StudentPage.DoesNotExist:
            raise Http404("Cannot find student")

        # Render response
        return render(request, self.student_template, {
            'self': self,
            'school': school,
            'programme': programme,
            'student': student,
        })

    def route_programme(self, request, school, programme, path_components):
        if path_components:
            # Request is for a student page
            if len(path_components) != 1:
                raise Http404("Students cannot have child pages")

            return self.serve_student(request,school,  programme, path_components[0])
        else:
            # Request is for a programme page
            return self.serve_programme(request, school, programme)

    def route_school(self, request, school, path_components):
        if path_components:
            # Request is for a programme or student page
            child_slug = path_components[0]
            remaining_components = path_components[1:]

            return self.route_programme(request, school, child_slug, remaining_components)
        else:
            # Request is for a school page
            return self.serve_school(request, school)

    def route(self, request, path_components):
        if path_components:
            # Request is for a child of this page
            child_slug = path_components[0]
            remaining_components = path_components[1:]

            # Try school index
            if not remaining_components and child_slug == 'schools':
                return self.serve_school_index(request)

            # Try school/programme/student
            try:
                return self.route_school(request, child_slug, remaining_components)
            except Http404:
                pass

            # Fallback to subpage
            try:
                subpage = self.get_children().get(slug=child_slug)
            except Page.DoesNotExist:
                raise Http404

            return subpage.specific.route(request, remaining_components)
        else:
            # Request is for landing page
            if self.live:
                return self.serve_landing(request)
            else:
                raise Http404

ShowIndexPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('year'),
    InlinePanel(ShowIndexPage, 'schools', label="Schools"),
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
