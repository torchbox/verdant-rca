import random
from django import template
from rca_show import models
from rca import models as rca_models

register = template.Library()


@register.simple_tag
def get_school_index_url(self):
    return self.get_school_index_url()


@register.simple_tag
def get_school_url(self, school):
    return self.get_school_url(school)


@register.simple_tag
def get_programme_url(self, school, programme):
    return self.get_programme_url(school, programme)


@register.simple_tag
def get_student_url(self, student):
    return self.get_student_url(student)


@register.simple_tag
def get_programme_display(programme):
    return dict(rca_models.ALL_PROGRAMMES)[programme]


@register.simple_tag
def get_school_display(school):
    return dict(rca_models.SCHOOL_CHOICES)[school]


@register.assignment_tag
def get_schools(self):
    return self.get_schools()


@register.assignment_tag
def get_school_programmes(self, school):
    return self.get_school_programmes(school)


@register.assignment_tag
def get_school_students(self, school, random = False):
    if random:
        return self.get_rand_students(school)
    else:
        return self.get_students(school)


@register.assignment_tag
def get_programme_students(self, school, programme, random = False):
    if random:
        return self.get_rand_students(school, programme)
    else:
        return self.get_students(school, programme)


@register.assignment_tag
def randsize(rangeStart, rangeEnd):
    return random.randrange(rangeStart, rangeEnd)


@register.assignment_tag
def secondary_menu(calling_page=None):
    pages = []
    if calling_page:
        pages = calling_page.get_children().filter(
            live=True,
            show_in_menus=True
        )

        print calling_page.get_children()

    print pages
    return pages
