from django import template


register = template.Library()


@register.simple_tag
def school_historical_display_name(school, year):
    return school.get_display_name_for_year(year)


@register.simple_tag
def programme_historical_display_name(programme, year):
    return programme.get_display_name_for_year(year)
