import random
from django import template
from rca.models import *
from datetime import date
from itertools import chain
from django.db.models import Min
from core.models import get_navigation_menu_items
from verdantdocs.models import Document

register = template.Library()

@register.inclusion_tag('rca/tags/upcoming_events.html', takes_context=True)
def upcoming_events(context, exclude=None, count=3):
    events = EventItem.future_objects.filter(live=True).annotate(start_date=Min('dates_times__date_from')).order_by('start_date')
    if exclude:
        events = events.exclude(id=exclude.id)
    return {
        'events': events[:count],
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/carousel_news.html', takes_context=True)
def news_carousel(context, area="", programme="", school="", count=6):
    if area:
        news_items = NewsItem.objects.filter(live=True, area=area)[:count]
    elif programme:
        news_items = NewsItem.objects.filter(live=True, related_programmes__programme=programme)[:count]
    elif school:
        news_items = NewsItem.objects.filter(live=True, related_schools__school=school)[:count]
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
        events = EventItem.future_objects.filter(live=True).annotate(start_date=Min('dates_times__date_from')).filter(related_schools__school=school).order_by('start_date')
    elif programme:
        events = EventItem.future_objects.filter(live=True).annotate(start_date=Min('dates_times__date_from')).filter(related_programmes__programme=programme).order_by('start_date')
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
    programmes = ProgrammePage.objects.filter(live=True, school=school)
    return {
        'programmes': programmes,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/staff_by_programme.html', takes_context=True)
def staff_by_programme(context, programme):
    staff = StaffPage.objects.filter(live=True, roles__programme=programme)
    return {
        'staff': staff,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/alumni_by_programme.html', takes_context=True)
def alumni_by_programme(context, programme):
    alumni = AlumniPage.objects.filter(live=True, programme=programme)
    return {
        'alumni': alumni,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/rca_now_related.html', takes_context=True)
def rca_now_related(context, programme="", author=""):
    if programme:
        rcanow = RcaNowPage.objects.filter(live=True, show_on_homepage=1).filter(programme=programme)
    elif author:
        rcanow = RcaNowPage.objects.filter(live=True, author=author)
    return {
        'rcanow_pages': rcanow,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/research_related.html', takes_context=True)
def research_related(context, programme="", person="", school="", exclude=None):
    if programme:
        research_items = ResearchItem.objects.filter(live=True, programme=programme)
    elif person:
        research_items = ResearchItem.objects.filter(live=True, creator__person=person)
    elif school:
        research_items = ResearchItem.objects.filter(live=True, school=school)
    if exclude:
        research_items = research_items.exclude(id=exclude.id)
    return {
        'research_items': research_items,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
        'person': person,
        'programme': programme,
        'school': school
    }

@register.inclusion_tag('rca/tags/rca_now_latest.html', takes_context=True)
def rca_now_latest(context, exclude=None, count=4):
    rcanow = RcaNowPage.objects.filter(live=True)
    if exclude:
        rcanow = rcanow.exclude(id=exclude.id)
    rcanow = rcanow.order_by('date')
    return {
        'rcanow_pages': rcanow[:count],
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/upcoming_jobs.html', takes_context=True)
def upcoming_jobs(context, exclude=None, count=6):
    jobs = JobPage.objects.filter(live=True, closing_date__gte=date.today()).order_by('closing_date')
    if exclude:
        jobs = jobs.exclude(id=exclude.id)
    return {
        'jobs': jobs[:count],
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/jobs_listing.html', takes_context=True)
def jobs_listing(context):
    jobs = JobPage.objects.filter(live=True, closing_date__gte=date.today()).order_by('closing_date')
    return {
        'jobs': jobs,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/students_related.html', takes_context=True)
def students_related(context, programme="", year="", exclude=None, count=4):
    students = StudentPage.objects.filter(live=True, programme=programme)
    students = students.filter(degree_year=year)
    if exclude:
        students = students.exclude(id=exclude.id)
    return {
        'students': students[:count],
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

# Queries students who 'have work' (i.e. have some carousel entries). Also matches degree year
@register.inclusion_tag('rca/tags/students_related_work.html', takes_context=True)
def students_related_work(context, year="", exclude=None, count=4):
    students = StudentPage.objects.filter(live=True, degree_year=year)
    students = students.filter(carousel_items__image__isnull=False) | students.filter(carousel_items__embedly_url__isnull=False)
    students=students.distinct()

    if exclude:
        students = students.exclude(id=exclude.id)
    return {
        'students': students[:count],
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/staff_random.html', takes_context=True)
def staff_random(context, exclude=None, count=4):
    staff = StaffPage.objects.filter(live=True).order_by('?')
    if exclude:
        staff = staff.exclude(id=exclude.id)
    return {
        'staff': staff[:count],
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/homepage_packery.html', takes_context=True)
def homepage_packery(context, news_count=5, staff_count=5, student_count=5, tweets_count=5, rcanow_count=5, standard_count=5, research_count=5, alumni_count=5):
    news = NewsItem.objects.filter(live=True, show_on_homepage=1).order_by('?')
    staff = StaffPage.objects.filter(live=True, show_on_homepage=1).order_by('?')
    student = StudentPage.objects.filter(live=True, show_on_homepage=1).order_by('?')
    rcanow = RcaNowPage.objects.filter(live=True, show_on_homepage=1).order_by('?')
    standard = StandardPage.objects.filter(live=True, show_on_homepage=1).order_by('?')
    research = ResearchItem.objects.filter(live=True, show_on_homepage=1).order_by('?')
    alumni = AlumniPage.objects.filter(live=True, show_on_homepage=1).order_by('?')
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
        pages = calling_page.get_children().filter(live=True, show_in_menus=True)
    return {
        'pages': pages,
        'calling_page': calling_page, # needed to get related links from the tag
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/research_students_feed.html', takes_context=True)
def research_students_feed(context, staff_page=None):
    students = StudentPage.objects.filter(live=True, supervisor=staff_page)
    return {
        'students': students,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/research_students_list.html', takes_context=True)
def research_students_list(context, staff_page=None):
    students = StudentPage.objects.filter(live=True, supervisor=staff_page)
    return {
        'students': students,
        'staff_page': staff_page, #needed to get the supervised_student_other field to list research students without profile pages
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

#queries all docs with a tag of 'jobapplication' - these are used for equal opportunites monitoring form etc which appear on every job page
@register.inclusion_tag('rca/tags/job_documents.html', takes_context=True)
def job_documents(context):
    documents = Document.objects.filter(tags__name = "job_application")
    return {
        'documents': documents,
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


def get_navigation_tree(max_depth=2, must_have_children=False):
    """
    do a thing
    """
    min_child_count = 1 if must_have_children else 0
    pages = Page.objects.raw("""
        SELECT * FROM core_page
        WHERE depth = 2
        OR (depth <= %(depth)s
        AND numchild >= %(min_child_count)s
        AND live = True
        AND show_in_menus = True)
        ORDER BY path
    """ % {
        'depth': str(max_depth),
        'min_child_count': str(min_child_count),
        })

    # Turn this into a tree structure:
    #     tree_node = (page, children)
    #     where 'children' is a list of tree_nodes.
    # Algorithm:
    # Similar to the core.models.get_navigation_menu_items() function, maintain
    # a list that tells us, for each depth level, the last page we saw at that
    # depth level.  Since our page list is ordered by path, we know that
    # whenever we see a page at depth d, its parent, _if_included_, must be the
    # last page we saw at depth (d-1), and so we can find it in that list.

    # Make a list of dummy nodes, since at any stage we may not have added the
    # parent to the list (i.e. it's unpublished or not to be shown in menus)
    depth_list = [(None, [])] * (max_depth + 1)

    for page in pages:
        # create a node for this page
        node = (page, [])
        try:
            # retrieve the parent from depth_list
            parent_page, parent_childlist = depth_list[page.depth - 1]
            if parent_page and page.path[:-4] == parent_page.path:
                # the page is an immediate descendant of the parent_page, so
                # insert this new node in the parent's child list
                parent_childlist.append(node)
        except IndexError:
            # we haven't seen any relevant pages at the parent's depth yet, so
            # don't add this page either
            pass

        # add the new node to depth_list
        try:
            depth_list[page.depth] = node
        except IndexError:
            # an exception here means that this node is one level deeper than any we've seen so far
            depth_list.append(node)

    try:
        root, root_children = depth_list[2] # start one level down from root, as we're not in the backend
        return root_children
    except IndexError:
        return []


@register.inclusion_tag('rca/tags/explorer_nav.html')
def menu():
    nodes = get_navigation_menu_items()[0][1]  # don't show the homepage
    return {
        'nodes': nodes,
    }


@register.inclusion_tag('rca/tags/explorer_nav.html')
def menu_subnav(nodes):
    return {
        'nodes': nodes,
    }


@register.inclusion_tag('rca/tags/footer_nav.html')
def footer_menu():
    nodes = get_navigation_tree(max_depth=5, must_have_children=False)
    return {
        'nodes': nodes,
    }
