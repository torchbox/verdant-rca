from django import template
from rca_show import models

register = template.Library()


@register.simple_tag(takes_context=True)
def programme_url(context, school, programme):
    return school.programme_url(programme)


@register.simple_tag(takes_context=True)
def student_url(context, school, student):
    return school.student_url(student)
