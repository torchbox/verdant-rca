from django.db import models
from django.http import Http404
from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from modelcluster.fields import ParentalKey
from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailcore.fields import RichTextField
from rca.models import StudentPage, SocialFields, SCHOOL_CHOICES, PROGRAMME_CHOICES


class ShowIndexPageSchool(Orderable):
    page = ParentalKey('rca_show.ShowIndexPage', related_name='schools')
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES)
    intro = RichTextField(blank=True)

    panels = [FieldPanel('school'), FieldPanel('intro')]

class ShowIndexPage(Page, SocialFields):
    year = models.CharField(max_length=4, blank=True)
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True)
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True)

    def get_students(self, school=None, programme=None):
        students = StudentPage.objects.filter(live=True)

        if self.year:
            students = students.filter(degree_year=self.year)

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
        # Check if there are students in this school
        if not self.get_students(school):
            raise Http404("No students found in this school")

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
        # Check if there are students in this programme
        if not self.get_students(school, programme):
            raise Http404("No students found in this programme")

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

    def route(self, request, path_components):
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

            if len(slugs) == 1:
                return self.serve_school(request, slugs[0])
            elif len(slugs) == 2:
                return self.serve_programme(request, slugs[0], slugs[1])
            elif len(slugs) == 3:
                return self.serve_student(request, slugs[0], slugs[1], slugs[2])

        if path_components:
            # Fallback to subpage
            child_slug = path_components[0]
            remaining_components = path_components[1:]
            try:
                subpage = self.get_children().get(slug=child_slug)
            except Page.DoesNotExist:
                raise Http404
        else:
            raise Http404

ShowIndexPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('year'),
    InlinePanel(ShowIndexPage, 'schools', label="Schools"),
    MultiFieldPanel([
        FieldPanel('school'),
        FieldPanel('programme'),
    ], "Scope"),
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
