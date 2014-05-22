import random
from django import template
from rca_show import models
from rca import models as rca_models, utils as rca_utils

register = template.Library()


@register.simple_tag
def show_subpage_url(show_index, name, *args, **kwargs):
    if show_index.is_programme_page and name in ['student', 'programme'] and 'school' in kwargs:
        del kwargs['school']

    return show_index.reverse_subpage(name, *args, **kwargs)


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
        return show_index.get_rand_students(school=school)
    else:
        return show_index.get_students(school=school)


@register.assignment_tag
def get_programme_students(show_index, programme, random = False):
    if show_index is None:
        return []

    if random:
        return show_index.get_rand_students(programme=programme)
    else:
        return show_index.get_students(programme=programme)


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


@register.assignment_tag
def get_maps_for_campus(campus):
    maps = models.ShowExhibitionMapPage.objects.filter(live=True, campus=campus)
   
    return maps


@register.assignment_tag
def get_school_for_programme(programme):
    return rca_utils.get_school_for_programme(programme)
