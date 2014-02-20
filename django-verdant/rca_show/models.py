from django.db import models
from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from wagtail.wagtailcore.models import Page
from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailcore.fields import RichTextField
from rca.models import StudentPage, SocialFields, SCHOOL_CHOICES


class ShowIndexPage(Page, SocialFields):
    year = models.CharField(max_length=4, blank=True)

    def get_schools(self):
        return ShowSchoolPage.objects.filter(live=True, path__startswith=self.path)

    def get_students(self):
        return StudentPage.objects.filter(live=True, degree_year=self.year)

    template = 'rca_show/index.html'
    def serve(self, request):
        # Render response
        return render(request, self.template, {
            'self': self,
            'schools': self.get_schools(),
        })

ShowIndexPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('year'),
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


class ShowSchoolPage(Page, SocialFields):
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES)
    body = RichTextField()

    def get_index(self):
        parent = self.get_parent().specific
        if not isinstance(parent, ShowIndexPage):
            raise Exception("Cannot find show index page")
        return parent

    def get_students(self, programme=None):
        students = self.get_index().get_students().filter(school=self.school)

        if programme:
            students = students.filter(programme=programme)

        return students

    def get_student(self, programme, slug):
        return self.get_students(programme).get(slug=slug)

    def get_programmes(self):
        return [
            values['programme']
            for values in self.get_students().order_by('programme').distinct('programme').values('programme')
        ]

    def programme_url(self, programme):
        return self.url + programme + '/'

    def student_url(self, student):
        return self.programme_url(student.programme) + student.slug + '/'

    # Views
    school_template = 'rca_show/school.html'
    programme_template = 'rca_show/programme.html'
    student_template = 'rca_show/student.html'

    def serve(self, request):
        # Render response
        return render(request, self.school_template, {
            'school_page': self,
        })

    def serve_programme(self, request, programme):
        # Get students for this programme
        students = self.get_students(programme)

        # If there are no students, this programme doesn't exist!
        if not students:
            raise Http404("No students exist with this programme")

        # Render response
        return render(request, self.programme_template, {
            'school_page': self,
            'programme': programme,
            'students': students,
        })

    def serve_student(self, request, programme, student):
        # Get the student
        try:
            student = self.get_student(programme, student)
        except StudentPage.DoesNotExist:
            raise Http404("Cannot find student")

        # Render response
        return render(request, self.student_template, {
            'school_page': self,
            'programme': programme,
            'student': student,
        })

    def route_programme(self, request, programme, path_components):
        if path_components:
            # Request is for a student page
            if len(path_components) != 1:
                raise Http404("Students cannot have child pages")

            return self.serve_student(request, programme, path_components[0])
        else:
            # Request is for a programme page
            return self.serve_programme(request, programme)

    def route(self, request, path_components):
        if path_components:
            # Request is for a child of this page
            child_slug = path_components[0]
            remaining_components = path_components[1:]

            # Try programme
            try:
                return self.route_programme(request, child_slug, remaining_components)
            except Http404:
                pass

            # Fallback to subpage
            try:
                subpage = self.get_children().get(slug=child_slug)
            except Page.DoesNotExist:
                raise Http404

            return subpage.specific.route(request, remaining_components)
        else:
            # Request is for this very page
            if self.live:
                return self.serve(request)
            else:
                raise Http404

ShowSchoolPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('body', classname="full"),
]

ShowSchoolPage.promote_panels = [
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

    FieldPanel('school'),
]