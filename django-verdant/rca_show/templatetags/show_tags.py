from django import template
from rca_show import models

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


@register.assignment_tag
def get_schools(self):
    return self.get_schools()


@register.assignment_tag
def get_school_programmes(self, school):
    return self.get_school_programmes(school)


@register.assignment_tag
def get_school_students(self, school):
    print "GET SCHOOL STUDENTS: " + school
    print self.get_students(school)
    return self.get_students(school)


@register.assignment_tag
def get_programme_students(self, school, programme):
    return self.get_students(school, programme)
