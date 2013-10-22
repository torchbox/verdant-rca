import random
from django import template
from rca.models import *
from datetime import date
from itertools import chain
from django.db.models import Min
from core.models import get_navigation_menu_items

register = template.Library()

@register.inclusion_tag('rca/tags/upcoming_events.html', takes_context=True)
def upcoming_events(context, exclude=None, count=3):
    events = EventItem.future_objects.annotate(start_date=Min('dates_times__date_from')).order_by('start_date')
    if exclude:
        events = events.exclude(id=exclude.id)
    return {
        'events': events[:count],
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/carousel_news.html', takes_context=True)
def news_carousel(context, area="", programme="", school="", count=6):
    if area:
        news_items = NewsItem.objects.filter(area=area)[:count]
    elif programme:
        news_items = NewsItem.objects.filter(related_programmes__programme=programme)[:count]
    elif school:
        news_items = NewsItem.objects.filter(related_schools__school=school)[:count]
    else:
        # neither programme nor area specified - return no results
        news_items = NewsItem.objects.none()

    return {
        'news_items': news_items,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/upcoming_events_related.html', takes_context=True)
def upcoming_events_related(context, opendays=0, programme="", school="", display_name="", events_index_url="/events/"):
    if school:
        events = EventItem.future_objects.annotate(start_date=Min('dates_times__date_from')).filter(related_schools__school=school).order_by('start_date')
    elif programme:
        events = EventItem.future_objects.annotate(start_date=Min('dates_times__date_from')).filter(related_programmes__programme=programme).order_by('start_date')
    if opendays:
        events = events.filter(audience='openday')
    else:
        events = events.exclude(audience='openday')
    return {
        'opendays': opendays,
        'events': events,
        'display_name': display_name,
        'school': school,
        'programme': programme,
        'events_index_url': events_index_url,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/programmes_by_school.html', takes_context=True)
def programme_by_school(context, school):
    programmes = ProgrammePage.objects.filter(school=school)
    return {
        'programmes': programmes,
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

@register.inclusion_tag('rca/tags/rca_now_related.html', takes_context=True)
def rca_now_related(context, programme="", author=""):
    if programme:
        rcanow = RcaNowPage.objects.filter(show_on_homepage=1).filter(programme=programme)
    elif author:
        rcanow = RcaNowPage.objects.filter(author=author)
    return {
        'rcanow_pages': rcanow,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/research_related.html', takes_context=True)
def research_related(context, programme="", person="", school="", exclude=None):
    if programme:
        research_items = ResearchItem.objects.filter(programme=programme)
    elif person:
        research_items = ResearchItem.objects.filter(creator__person=person)
    elif school:
        research_items = ResearchItem.objects.filter(school=school)
    if exclude:
        research_items = research_items.exclude(id=exclude.id)
    return {
        'research_items': research_items,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/rca_now_latest.html', takes_context=True)
def rca_now_latest(context, exclude=None, count=4):
    rcanow = RcaNowPage.objects.all()
    if exclude:
        rcanow = rcanow.exclude(id=exclude.id)
    rcanow = rcanow.order_by('date')
    return {
        'rcanow_pages': rcanow[:count],
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/upcoming_jobs.html', takes_context=True)
def upcoming_jobs(context, exclude=None, count=6):
    jobs = JobPage.objects.filter(closing_date__gte=date.today()).order_by('closing_date')
    if exclude:
        jobs = jobs.exclude(id=exclude.id)
    return {
        'jobs': jobs[:count],
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/jobs_listing.html', takes_context=True)
def jobs_listing(context):
    jobs = JobPage.objects.filter(closing_date__gte=date.today()).order_by('closing_date')
    return {
        'jobs': jobs,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/students_related.html', takes_context=True)
def students_related(context, programme="", exclude=None, count=4):
    students = StudentPage.objects.filter(programme=programme)
    if exclude:
        students = students.exclude(id=exclude.id)
    return {
        'students': students[:count],
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/staff_random.html', takes_context=True)
def staff_random(context, exclude=None, count=4):
    staff = StaffPage.objects.all().order_by('?')
    if exclude:
        staff = staff.exclude(id=exclude.id)
    return {
        'staff': staff[:count],
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/homepage_packery.html', takes_context=True)
def homepage_packery(context, news_count=5, staff_count=5, student_count=5, tweets_count=5, rcanow_count=5, standard_count=5, research_count=5, alumni_count=5):
    news = NewsItem.objects.filter(show_on_homepage=1).order_by('?')
    staff = StaffPage.objects.filter(show_on_homepage=1).order_by('?')
    student = StudentPage.objects.filter(show_on_homepage=1).order_by('?')
    rcanow = RcaNowPage.objects.filter(show_on_homepage=1).order_by('?')
    standard = StandardPage.objects.filter(show_on_homepage=1).order_by('?')
    research = ResearchItem.objects.filter(show_on_homepage=1).order_by('?')
    alumni = AlumniPage.objects.filter(show_on_homepage=1).order_by('?')
    tweets = [[],[],[],[],[]]

    packeryItems =list(chain(news[:news_count], staff[:staff_count], student[:student_count], rcanow[:rcanow_count], standard[:standard_count], research[:research_count], alumni[:alumni_count], tweets[:tweets_count]))
    random.shuffle(packeryItems)

    return {
        'packery': packeryItems,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/sidebar_links.html', takes_context=True)
def sidebar_links(context, calling_page=None):
    if calling_page:
        pages = calling_page.get_children().filter(show_in_menus=True)
    return {
        'pages': pages,
        'calling_page': calling_page, # needed to get related links from the tag
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.filter
def content_type(value):
    return value.__class__.__name__.lower()

@register.filter
def paragraph_split(value, sep = "</p>"):
    parts = value.split(sep)
    return (parts[0], sep.join(parts[1:]))

@register.filter
def title_split(value):
    return value.split(' ')


@register.inclusion_tag('rca/tags/explorer_nav.html')
def menu(current_page=None):
    nodes = get_navigation_menu_items(depth=4)
    return {
        'nodes': nodes,
    }


@register.inclusion_tag('rca/tags/explorer_nav.html')
def menu_subnav(nodes):
    return {
        'nodes': nodes,
    }
