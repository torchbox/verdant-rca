from django.conf import settings

from rca.models import YEARS, SCHOOL_PROGRAMME_MAP, SCHOOL_CHOICES, ALL_PROGRAMMES, PROGRAMME_CHOICES, EVENT_LOCATION_CHOICES, AREA_CHOICES, EVENT_AUDIENCE_CHOICES, RESEARCH_TYPES_CHOICES, WORK_THEME_CHOICES, WORK_TYPES_CHOICES, STAFF_TYPES_CHOICES, INNOVATIONRCA_PROJECT_TYPES_CHOICES, SHOW_SCHOOLS, SUSTAINRCA_CATEGORY_CHOICES
from reachout_choices import REACHOUT_PROJECT_CHOICES, REACHOUT_PARTICIPANTS_CHOICES, REACHOUT_THEMES_CHOICES, REACHOUT_PARTNERSHIPS_CHOICES
from datetime import date


def global_vars(request):
    year = date.today().year

    try:
        schools_current_year = SCHOOL_PROGRAMME_MAP[str(year)].keys()
    except KeyError:
        # If there's no academic year specified for the current year then choose the last one.
        year = int(sorted(SCHOOL_PROGRAMME_MAP.keys())[-1])
        schools_current_year = SCHOOL_PROGRAMME_MAP[str(year)].keys()

    schools_current_year = filter(lambda s: s[0] in schools_current_year, SCHOOL_CHOICES)

    years_until_current_year = [y for y in YEARS if int(y) <= year]

    academic_year = '%s/%s' % (year - 1, str(year)[2:])  # 2015 -> 2014/15
    global_programmes = dict(PROGRAMME_CHOICES)[academic_year]

    return {
        'global_all_schools': SCHOOL_CHOICES,
        'global_schools': schools_current_year,
        'global_show_schools': SHOW_SCHOOLS,
        'global_all_programmes': ALL_PROGRAMMES,
        'global_programmes': global_programmes,
        'global_locations': EVENT_LOCATION_CHOICES,
        'global_areas': AREA_CHOICES,
        'global_years': years_until_current_year,
        'global_audiences': EVENT_AUDIENCE_CHOICES,
        'global_research_types': RESEARCH_TYPES_CHOICES,
        'global_work_themes': WORK_THEME_CHOICES,
        'global_work_types': WORK_TYPES_CHOICES,
        'global_staff_types': STAFF_TYPES_CHOICES,
        'global_innovationrca_project_types': INNOVATIONRCA_PROJECT_TYPES_CHOICES,
        'global_events_index_url': '/news-and-events/events/',
        'global_news_index_url': '/news-and-events/news/',
        'global_default_twitter_handle': "RCAevents",
        'global_reachout_projects': REACHOUT_PROJECT_CHOICES,
        'global_reachout_participants': REACHOUT_PARTICIPANTS_CHOICES,
        'global_reachout_themes': REACHOUT_THEMES_CHOICES,
        'global_reachout_partnerships': REACHOUT_PARTNERSHIPS_CHOICES,
        'global_categories': SUSTAINRCA_CATEGORY_CHOICES,
        'GOOGLE_ANALYTICS_ACCOUNT': settings.GOOGLE_ANALYTICS_ACCOUNT,
    }
