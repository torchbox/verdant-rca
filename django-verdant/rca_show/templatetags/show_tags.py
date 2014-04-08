import random
from django import template
from rca_show import models
from rca import models as rca_models

register = template.Library()

@register.simple_tag
def get_school_index_url(show_index):
    if show_index is None:
        return ''

    return show_index.get_school_index_url()


@register.simple_tag
def get_school_url(show_index, school):
    if show_index is None:
        return ''

    return show_index.get_school_url(school)


@register.simple_tag
def get_programme_url(show_index, school, programme):
    if show_index is None:
        return ''

    return show_index.get_programme_url(school, programme)


@register.simple_tag
def get_student_url(show_index, student):
    if show_index is None:
        return ''

    return show_index.get_student_url(student)


@register.simple_tag
def get_programme_display(programme):

    return dict(rca_models.ALL_PROGRAMMES)[programme]


@register.simple_tag
def get_school_display(school):

    return dict(rca_models.SCHOOL_CHOICES)[school]


@register.assignment_tag
def get_schools(show_index):
    if show_index is None:
        return []

    return show_index.get_schools()


@register.assignment_tag
def get_school_programmes(show_index, school):
    if show_index is None:
        return []

    return show_index.get_school_programmes(school)


@register.assignment_tag
def get_school_students(show_index, school, random = False):
    if show_index is None:
        return []

    if random:
        return show_index.get_rand_students(school)
    else:
        return show_index.get_students(school)


@register.assignment_tag
def get_programme_students(show_index, school, programme, random = False):
    if show_index is None:
        return []

    if random:
        return show_index.get_rand_students(school, programme)
    else:
        return show_index.get_students(school, programme)


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

    return pages


@register.assignment_tag(takes_context=True)
def get_show_index(context):
    if isinstance(context['self'], models.ShowIndexPage):
        return context['self']
    if hasattr(context['request'], 'show_index'):
        return context['request'].show_index
    if hasattr(context['self'], 'get_show_index'):
        return context['self'].get_show_index()

@register.assignment_tag(takes_context=True)
def get_maps_for_campus(context, campus):
    maps = models.ShowExhibitionMapPage.objects.filter(live=True, campus=campus)
   
    return maps
