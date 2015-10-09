from django import template
from django.core.cache import cache
from django.utils.html import conditional_escape
from django.db.models import Min, Max, Q, get_app, get_models, get_model
from django.template.base import parse_bits
from wagtail.wagtailcore.utils import camelcase_to_underscore

from datetime import date
from itertools import chain
import random
import re

from rca.models import *
from rca.utils import get_students
from wagtail.wagtaildocs.models import Document

register = template.Library()

@register.filter(name='fieldtype')
def fieldtype(bound_field):
    return camelcase_to_underscore(bound_field.field.__class__.__name__)

@register.inclusion_tag('rca/tags/upcoming_events.html', takes_context=True)
def upcoming_events(context, exclude=None, count=3, collapse_by_default=False):
    events = EventItem.future_not_current_objects.filter(live=True).only('id', 'url_path', 'title', 'audience').annotate(start_date=Min('dates_times__date_from'), end_date=Max('dates_times__date_to'))
    if exclude:
        events = events.exclude(id=exclude.id)

    return {
        'collapse_by_default': collapse_by_default,
        'events': events[:count],
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/carousel_news.html', takes_context=True)
def news_carousel(context, area="", programme="", school="", count=5):
    if area:
        news_items = NewsItem.objects.filter(live=True, areas__area=area)
    elif programme:
        news_items = NewsItem.objects.filter(live=True, related_programmes__programme__in=get_programme_synonyms(programme))
    elif school:
        news_items = NewsItem.objects.filter(live=True, related_schools__school=school)
    else:
        # neither programme nor area specified - return no results
        news_items = NewsItem.objects.none()

    # Order by reverse date and truncate
    news_items = news_items.order_by('-date')[:count]

    return {
        'news_items': news_items,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
        'news_index_url': context['global_news_index_url'],
    }

@register.inclusion_tag('rca/tags/upcoming_events_related.html', takes_context=True)
def upcoming_events_related(context, opendays=0, programme="", school="", display_name="", area="", audience=""):
    events = EventItem.future_objects.filter(live=True).annotate(start_date=Min('dates_times__date_from'))
    if school:
        events = events.filter(related_schools__school=school).order_by('start_date')
    elif programme:
        events = events.filter(related_programmes__programme__in=get_programme_synonyms(programme)).order_by('start_date')
    elif area:
        events = events.filter(area=area).order_by('start_date')
    elif audience:
        events = events.filter(audience=audience).order_by('start_date')
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
        'area': area,
        'audience': audience,
        'events_index_url': context['global_events_index_url'],
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
    staff = StaffPage.objects.filter(live=True, roles__programme__in=get_programme_synonyms(programme))
    return {
        'staff': staff,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/related_staff.html', takes_context=True)
def related_staff(context, programme="", school=""):
    if school:
        staff = StaffPage.objects.filter(live=True, roles__school=school)
    if programme:
        staff = StaffPage.objects.filter(live=True, roles__programme__in=get_programme_synonyms(programme))
    return {
        'staff': staff,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/alumni_by_programme.html', takes_context=True)
def alumni_by_programme(context, programme):
    alumni = AlumniPage.objects.filter(live=True, programme__in=get_programme_synonyms(programme))
    return {
        'alumni': alumni,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/rca_now_related.html', takes_context=True)
def rca_now_related(context, programme="", author=""):
    if programme:
        rcanow = RcaNowPage.objects.filter(live=True).filter(programme__in=get_programme_synonyms(programme))
    elif author:
        rcanow = RcaNowPage.objects.filter(live=True, author=author)
    return {
        'rcanow_pages': rcanow,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/research_related.html', takes_context=True)
def research_related(context, programme="", person="", school="", exclude=None):
    if programme:
        research_items = ResearchItem.objects.filter(live=True, programme__in=get_programme_synonyms(programme))
    elif person:
        research_items = ResearchItem.objects.filter(live=True, creator__person=person)
    elif school:
        research_items = ResearchItem.objects.filter(live=True, school=school)
    if exclude:
        research_items = research_items.exclude(id=exclude.id)
    return {
        'research_items': research_items.order_by('?'),
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
        'person': person,
        'programme': programme,
        'school': school
    }

@register.inclusion_tag('rca/tags/innovation_rca_related.html', takes_context=True)
def innovation_rca_related(context, programme="", person="", school="", exclude=None):
    if programme:
        projects = InnovationRCAProject.objects.filter(live=True, programme__in=get_programme_synonyms(programme))
    elif person:
        projects = InnovationRCAProject.objects.filter(live=True, creator__person=person)
    elif school:
        projects = InnovationRCAProject.objects.filter(live=True, school=school)
    if exclude:
        projects = projects.exclude(id=exclude.id)
    return {
        'projects': projects.order_by('?'),
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
        'person': person,
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

def get_related_students(programme=None, year=None, exclude=None, has_work=False):
    ma_students_q = ~Q(ma_school='')
    mphil_students_q = ~Q(mphil_school='')
    phd_students_q = ~Q(phd_school='')

    if has_work:
        ma_students_q &= (Q(show_carousel_items__image__isnull=False) | Q(show_carousel_items__embedly_url__isnull=False))
        mphil_students_q &= (Q(mphil_carousel_items__image__isnull=False) | Q(mphil_carousel_items__embedly_url__isnull=False))
        phd_students_q &= (Q(phd_carousel_items__image__isnull=False) | Q(phd_carousel_items__embedly_url__isnull=False))

    if programme:
        ma_students_q &= Q(ma_programme__in=get_programme_synonyms(programme))
        mphil_students_q &= Q(mphil_programme__in=get_programme_synonyms(programme))
        phd_students_q &= Q(phd_programme__in=get_programme_synonyms(programme))

    if year:
        ma_students_q &= Q(ma_graduation_year=year)
        mphil_students_q &= Q(mphil_start_year=year)
        phd_students_q &= Q(phd_start_year=year)

    students = NewStudentPage.objects.filter(live=True).filter(ma_students_q | mphil_students_q | phd_students_q).order_by('?')

    if exclude:
        students = students.exclude(id=exclude.id)

    return students

@register.inclusion_tag('rca/tags/students_related.html', takes_context=True)
def students_related(context, programme=None, year=None, exclude=None, count=4):
    return {
        'students': get_related_students(programme=programme, year=year, exclude=exclude, has_work=False)[:count],
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

# Queries students who 'have work' (i.e. have some carousel entries). Also matches degree year
@register.inclusion_tag('rca/tags/students_related_work.html', takes_context=True)
def students_related_work(context, year=None, exclude=None, count=4):
    return {
        'students': get_related_students(year=year, exclude=exclude, has_work=True)[:count],
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/staff_random.html', takes_context=True)
def staff_random(context, exclude=None, programmes=None, count=4):
    staff = StaffPage.objects.filter(live=True).order_by('?')
    if exclude:
        staff = staff.exclude(id=exclude.id)
    if programmes:
        programmes = sum([get_programme_synonyms(programme) for programme in programmes], [])
        staff = staff.filter(roles__programme__in=programmes)
    return {
        'staff': staff[:count],
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/staff_related.html', takes_context=True)
def staff_related(context, staff_page, count=4):
    staff = StaffPage.objects.filter(live=True).exclude(id=staff_page.id).order_by('?')
    # import pdb; pdb.set_trace()
    if staff_page.programmes:
        programmes = sum([get_programme_synonyms(programme) for programme in staff_page.programmes], [])
        staff = staff.filter(roles__programme__in=programmes)
    elif staff_page.school:
        staff = staff.filter(school=staff_page.school)
    return {
        'staff': staff[:count],
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/homepage_packery.html', takes_context=True)
def homepage_packery(context, calling_page=None, news_count=5, staff_count=5, student_count=5, tweets_count=5, rcanow_count=5, research_count=5, alumni_count=5, review_count=5, blog_count=5):
    news = NewsItem.objects.filter(live=True, show_on_homepage=1).order_by('?')
    staff = StaffPage.objects.filter(live=True, show_on_homepage=1).order_by('?')
    student = NewStudentPage.objects.filter(live=True, show_on_homepage=1).order_by('?')
    rcanow = RcaNowPage.objects.filter(live=True, show_on_homepage=1).order_by('?')
    research = ResearchItem.objects.filter(live=True, show_on_homepage=1).order_by('?')
    alumni = AlumniPage.objects.filter(live=True, show_on_homepage=1).order_by('?')
    review = ReviewPage.objects.filter(live=True, show_on_homepage=1).order_by('?')
    blog = RcaBlogPage.objects.filter(live=True, show_on_homepage=1).order_by('?')
    tweets = [[],[],[],[],[]]

    packeryItems =list(chain(news[:news_count], staff[:staff_count], student[:student_count], rcanow[:rcanow_count], research[:research_count], alumni[:alumni_count], review[:review_count], tweets[:tweets_count], blog[:blog_count]))
    random.shuffle(packeryItems)

    return {
        'calling_page': calling_page,
        'packery': packeryItems,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/sidebar_adverts.html', takes_context=True)
def sidebar_adverts(context, show_open_days=False):
    return {
        'global_adverts': Advert.objects.filter(show_globally=True),
        'show_open_days': show_open_days,
        'self': context.get('self'),
        'global_events_index_url': context['global_events_index_url'],
        'request': context['request'],
    }

@register.inclusion_tag('rca/tags/sidebar_links.html', takes_context=True)
def sidebar_links(context, calling_page=None):
    if calling_page:
        pages = calling_page.get_children().filter(live=True, show_in_menus=True)

        # If no children, get siblings instead
        if len(pages) == 0:
            pages = calling_page.get_siblings(inclusive=False).filter(live=True, show_in_menus=True)
    return {
        'pages': pages,
        'calling_page': calling_page, # needed to get related links from the tag
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/research_students_feed.html', takes_context=True)
def research_students_feed(context, staff_page=None):
    students = NewStudentPage.objects.filter(live=True).filter(Q(mphil_supervisors__supervisor=staff_page) | Q(phd_supervisors__supervisor=staff_page))
    return {
        'students': students,
        'request': context['request'],  # required by the {% pageurl %} tag that we want to use within this template
    }

@register.inclusion_tag('rca/tags/research_students_list.html', takes_context=True)
def research_students_list(context, staff_page=None):
    students = NewStudentPage.objects.filter(live=True).filter(Q(mphil_supervisors__supervisor=staff_page) | Q(phd_supervisors__supervisor=staff_page))
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
    value = re.sub('\n', ' ', value)
    value = re.sub('<p>\s*</p>', ' ', value)
    parts = value.split(sep)
    return (parts[0], sep.join(parts[1:]))

@register.filter
def title_split(value):
    return value.split(' ')


def get_site_nav(max_depth=2, must_have_children=False, only_in_menu_pages=True):
    """
    Return a tree structure of all pages, optionally limiting to those with
    children and those with 'show_in_menus = True'

    Set max_depth=0 in order not to filter by depth

    """
    min_child_count = 1 if must_have_children else 0
    menu_filter = 'AND show_in_menus = True' if only_in_menu_pages else ''
    # we add 2 to max_depth, as admin 'root' has depth 1, and site home has
    # depth 2 thus max_depth=3 will become SQL 'AND depth <= 5', and will
    # burrow 3 levels down from site home
    depth_filter = 'AND depth <= %s' % (max_depth + 2) if max_depth else ''

    pages = Page.objects.raw("""
        SELECT * FROM wagtailcore_page
        WHERE depth = 2
        OR (
        live = True
        AND numchild >= %(min_child_count)s
        %(depth_filter)s
        %(menu_filter)s
        )
        ORDER BY path
    """ % {
        'min_child_count': str(min_child_count),
        'depth_filter': depth_filter,
        'menu_filter': menu_filter,
        })

    # Turn this into a tree structure:
    #     tree_node = (page, children)
    #     where 'children' is a list of tree_nodes.
    # Algorithm:
    # Similar to the wagtailcore.models.get_navigation_menu_items() function, maintain
    # a list that tells us, for each depth level, the last page we saw at that
    # depth level.  Since our page list is ordered by path, we know that
    # whenever we see a page at depth d, its parent, _if_included_, must be the
    # last page we saw at depth (d-1), and so we can find it in that list.

    # Make a list of dummy nodes, since at any stage we may not have added the
    # parent to the list (i.e. it's unpublished or not to be shown in menus)
    depth_list = [(None, [])] * max([p.depth for p in pages])

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


@register.inclusion_tag('rca/tags/explorer_nav.html', takes_context=True)
def menu(context):
    nodes = get_site_nav(max_depth=4, must_have_children=False, only_in_menu_pages=True)
    return {
        'nodes': nodes,
        'request': context['request'],
    }


@register.inclusion_tag('rca/tags/explorer_nav.html', takes_context=True)
def menu_subnav(context, nodes):
    return {
        'nodes': nodes,
        'request': context['request'],
    }


@register.inclusion_tag('rca/tags/footer_nav.html', takes_context=True)
def footer_menu(context):
    nodes = get_site_nav(max_depth=3, must_have_children=False, only_in_menu_pages=True)
    return {
        'nodes': nodes,
        'request': context['request'],
    }


@register.filter
def rows_distributed(thelist, n):
    """
    Break a list into ``n`` 'rows', distributing columns as evenly as possible
    across the rows. For example::

        >>> l = range(10)

        >>> rows_distributed(l, 2)
        [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9]]

        >>> rows_distributed(l, 3)
        [[0, 1, 2, 3], [4, 5, 6], [7, 8, 9]]

        >>> rows_distributed(l, 4)
        [[0, 1, 2], [3, 4, 5], [6, 7], [8, 9]]

        >>> rows_distributed(l, 5)
        [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]]

        >>> rows_distributed(l, 9)
        [[0, 1], [2], [3], [4], [5], [6], [7], [8], [9]]

        # This filter will always return `n` rows, even if some are empty:
        >>> rows(range(2), 3)
        [[0], [1], []]

    Taken from https://djangosnippets.org/snippets/401/
    """
    try:
        n = int(n)
        thelist = list(thelist)
    except (ValueError, TypeError):
        return [thelist]
    list_len = len(thelist)
    split = list_len // n

    remainder = list_len % n
    offset = 0
    rows = []
    for i in range(n):
        if remainder:
            start, end = (split+1)*i, (split+1)*(i+1)
        else:
            start, end = split*i+offset, split*(i+1)+offset
        rows.append(thelist[start:end])
        if remainder:
            remainder -= 1
            offset += 1
    return rows


@register.filter
def time_display(time):
    # Get hour and minute from time object
    hour = time.hour
    minute = time.minute

    # Convert to 12 hour format
    if hour >= 12:
        pm = True
        hour -=12
    else:
        pm = False
    if hour == 0:
        hour = 12

    # Hour string
    hour_string = str(hour)

    # Minute string
    if minute != 0:
        minute_string = "." + str(minute)
    else:
        minute_string = ""

    # PM string
    if pm:
        pm_string = "pm"
    else:
        pm_string = "am"

    # Join and return
    return "".join([hour_string, minute_string, pm_string])


@register.tag
def tabdeck(parser, token):
    bits = token.split_contents()[1:]
    args, kwargs = parse_bits(parser, bits, [], 'args', 'kwargs', None, False, 'tabdeck')

    nodelist = parser.parse(('endtabdeck',))
    parser.delete_first_token()  # discard the 'endtabdeck' tag
    return TabDeckNode(nodelist, kwargs)

class TabDeckNode(template.Node):
    def __init__(self, nodelist, kwargs):
        self.nodelist = nodelist
        self.module_title_expr = kwargs.get('moduletitle')

    def render(self, context):
        context['tabdeck'] = {'tab_headings': [], 'index': 1}
        output = self.nodelist.render(context)  # run the contents of the tab; any {% tab %} tags within it will populate tabdeck.tab_headings
        headings = context['tabdeck']['tab_headings']

        if not headings:
            return ''

        tab_headers = [
            """<li%s><a class="t0">%s</a></li>""" % ((' class="active"' if i == 0 else ''), conditional_escape(heading))
            for i, heading in enumerate(headings)
        ]
        tab_header_html = """<ul class="tab-nav tabs-%d">%s</ul>""" % (len(headings), ''.join(tab_headers))
        module_title_html = '';
        if self.module_title_expr:
            module_title_html = '<h2 class="module-title">%s</h2>' % self.module_title_expr.resolve(context)
        return '<section class="row module tabdeck">' + module_title_html + tab_header_html + '<div class="tab-content">' + output + '</div></section>'


@register.tag
def tab(parser, token):
    bits = token.split_contents()[1:]
    args, kwargs = parse_bits(parser, bits, ['heading_expr'], 'args', 'kwargs', None, False, 'tab')

    if len(args) != 1:
        raise template.TemplateSyntaxError("The 'tab' tag requires exactly one unnamed argument (the tab heading).")

    heading_expr = args[0]

    nodelist = parser.parse(('endtab',))
    parser.delete_first_token()  # discard the 'endtab' tag
    return TabNode(nodelist, heading_expr, kwargs)

class TabNode(template.Node):
    def __init__(self, nodelist, heading_expr, kwargs):
        self.nodelist = nodelist
        self.heading_expr = heading_expr
        self.extra_classname_expr = kwargs.get('class')

    def render(self, context):
        heading = self.heading_expr.resolve(context)
        tab_content = self.nodelist.render(context)
        if not tab_content.strip():
            # tab content is empty; skip outputting the container elements,
            # and skip updating the tabdeck template vars so that it isn't allocated a heading
            return ''

        header_html = """<h2 class="header"><a class="a0%s">%s</a></h2>""" % (
            (' active' if context['tabdeck']['index'] == 1 else ''),
            conditional_escape(heading)
        )
        if self.extra_classname_expr:
            classname = "tab-pane %s" % self.extra_classname_expr.resolve(context)
        else:
            classname = "tab-pane"

        if context['tabdeck']['index'] == 1:
            classname += ' active'

        context['tabdeck']['tab_headings'].append(heading)
        context['tabdeck']['index'] += 1

        return header_html + ('<div class="%s">' % classname) + self.nodelist.render(context) + '</div>'

# settings value
@register.assignment_tag
def get_debug():
    return getattr(settings, 'DEBUG', "")


@register.assignment_tag
def get_student_carousel_items(student, degree=None, show_animation_videos=False):
    profile = student.get_profile(degree)
    carousel_items = profile['carousel_items'].all()

    # If this is an animation student, remove the first two carousel items if they are vimeo videos
    if show_animation_videos == False and get_students(degree_filters=dict(programme__in=['animation', 'visualcommunication'])).filter(id=student.id).exists():
        for i in range(2):
            try:
                first_carousel_item = carousel_items[0]
                if first_carousel_item and first_carousel_item.embedly_url:
                    carousel_items = carousel_items[1:]
            except IndexError:
                pass

    return carousel_items


def get_lightbox_config():

    excluded = []

    DONT_OPEN_IN_LIGHTBOX = [
        'rca.ProgrammePage',
        'rca.SchoolPage',
        'rca.GalleryPage',
        'rca.DonationPage',
        'rca.StreamPage',
        'rca_show.ShowStreamPage',
    ]  # 'rca.OEFormPage'

    for path in DONT_OPEN_IN_LIGHTBOX:
        app, model_name = path.split('.')
        for m in get_models(get_app(app)):
            if not issubclass(m, Page):
                continue
            if m.__name__.lower() == model_name.lower():
                excluded += list(m.objects.all().only('slug').values_list('slug', flat=True).distinct())
            if 'index' in m.__name__.lower() and m.__name__.lower() != 'standardindex':
                excluded += list(m.objects.all().only('slug').values_list('slug', flat=True).distinct())

    excluded1 = '/(%s)/?[\?#]?[^/]*$' % '|'.join(excluded)

    # don't open anything that's under a ShowIndexPage
    slugs = get_model('rca_show', 'ShowIndexPage').objects.all().only('slug').values_list('slug', flat=True).distinct()
    excluded2 = '/(%s)/.*' % '|'.join(slugs)

    return {
        'excluded1': excluded1,
        'excluded2': excluded2,
    }


@register.inclusion_tag('rca/includes/use_lightbox.html', takes_context=True)
def use_lightbox(context):
    if not 'self' in context:
        return {}

    cache_key = 'lightbox_config'
    lightbox_config = cache.get(cache_key)
    if not lightbox_config:
        lightbox_config = get_lightbox_config()
        cache.set(cache_key, lightbox_config, 60 * 60)

    return lightbox_config
