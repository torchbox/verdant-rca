from django import template

from rca.models import EventItem, NewsItem, StaffPage, AlumniPage, RcaNowPage, ResearchItem, JobPage
from datetime import date
from django.db.models import Min, Max

register = template.Library()

# FIXME: order by should really be on the first dates_times object
@register.inclusion_tag('rca/tags/upcoming_events.html', takes_context=True)
def upcoming_events(context, exclude=None, count=3):
    events = EventItem.objects.annotate(start_date=Min('dates_times__date_from'), end_date=Max('dates_times__date_to')).filter(end_date__gte=date.today()).order_by('start_date')
    if exclude:
        events = events.exclude(id=exclude.id)
    return {
        'events': events[:count],
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/carousel_news.html', takes_context=True)
def news_carousel(context, area="", programme="", count=6):
    if area:
        news_items = NewsItem.objects.filter(area=area)[:count]
    elif programme:
        news_items = NewsItem.objects.filter(related_programmes__programme=programme)[:count]
    else:
        # neither programme nor area specified - return no results
        news_items = NewsItem.objects.none()

    return {
        'news_items': news_items,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/upcoming_events_by_programme.html', takes_context=True)
def upcoming_events_by_programme(context, opendays=0, programme="", programme_display_name=""):
    events = EventItem.objects.annotate(start_date=Min('dates_times__date_from'), end_date=Max('dates_times__date_to')).filter(end_date__gte=date.today()).filter(related_programmes__programme=programme).order_by('start_date')
    if opendays:
        events = events.filter(audience='openday')
    else:
        events = events.exclude(audience='openday')
    return {
        'opendays': opendays,
        'events': events,
        'programme_display_name': programme_display_name,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/staff_by_programme.html', takes_context=True)
def staff_by_programme(context, programme):
    staff = StaffPage.objects.filter(roles__programme=programme)
    return {
        'staff': staff,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/alumni_by_programme.html', takes_context=True)
def alumni_by_programme(context, programme):
    alumni = AlumniPage.objects.filter(programme=programme)
    return {
        'alumni': alumni,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/rca_now_by_programme.html', takes_context=True)
def rca_now_by_programme(context, programme):
    rcanow = RcaNowPage.objects.filter(show_on_homepage=1).filter(programme=programme)
    return {
        'rcanow_pages': rcanow,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/research_by_programme.html', takes_context=True)
def research_by_programme(context, programme, exclude=None):
    research_items = ResearchItem.objects.filter(programme=programme)
    if exclude:
        research_items = research_items.exclude(id=exclude.id)
    return {
        'research_items': research_items,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/rca_now_latest.html', takes_context=True)
def rca_now_latest(context, exclude=None, count=4):
    # FIXME: needs ordering by date added
    rcanow = RcaNowPage.objects.all()
    if exclude:
        rcanow = rcanow.exclude(id=exclude.id)
    return {
        'rcanow_pages': rcanow[:count],
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/upcoming_jobs.html', takes_context=True)
def upcoming_jobs(context, exclude=None, count=6):
    jobs = JobPage.objects.filter(closing_date__gte=date.today())
    if exclude:
        jobs = jobs.exclude(id=exclude.id)
    return {
        'jobs': jobs[:count],
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }
