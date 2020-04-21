from django.conf import settings

from taxonomy.models import Programme, School, Area

from .models import (
    EVENT_LOCATION_CHOICES, EVENT_AUDIENCE_CHOICES,
    RESEARCH_TYPES_CHOICES, WORK_THEME_CHOICES, WORK_TYPES_CHOICES,
    STAFF_TYPES_CHOICES, INNOVATIONRCA_PROJECT_TYPES_CHOICES,
    SUSTAINRCA_CATEGORY_CHOICES
)
from .reachout_choices import REACHOUT_PROJECT_CHOICES, REACHOUT_PARTICIPANTS_CHOICES, REACHOUT_THEMES_CHOICES, REACHOUT_PARTNERSHIPS_CHOICES
from rca.navigation import Navigation


def global_vars(request):
    all_areas = Area.objects.all()
    all_schools = School.objects.all()
    all_programmes = Programme.objects.all()

    return {
        'global_all_schools': all_schools.values_list('slug', 'display_name'),
        'global_all_programmes': all_programmes.values_list('slug', 'display_name'),
        'global_locations': EVENT_LOCATION_CHOICES,
        'global_areas': all_areas.values_list('slug', 'display_name'),
        'global_audiences': EVENT_AUDIENCE_CHOICES,
        'global_research_types': RESEARCH_TYPES_CHOICES,
        'global_work_themes': WORK_THEME_CHOICES,
        'global_work_types': WORK_TYPES_CHOICES,
        'global_staff_types': STAFF_TYPES_CHOICES,
        'global_innovationrca_project_types': INNOVATIONRCA_PROJECT_TYPES_CHOICES,
        'global_events_index_url': '/news-and-events/events/',
        'global_news_index_url': '/news-and-events/news/',
        'global_default_twitter_handle': "RCA",
        'global_reachout_projects': REACHOUT_PROJECT_CHOICES,
        'global_reachout_participants': REACHOUT_PARTICIPANTS_CHOICES,
        'global_reachout_themes': REACHOUT_THEMES_CHOICES,
        'global_reachout_partnerships': REACHOUT_PARTNERSHIPS_CHOICES,
        'global_categories': SUSTAINRCA_CATEGORY_CHOICES,
        'GOOGLE_ANALYTICS_ACCOUNT': settings.GOOGLE_ANALYTICS_ACCOUNT,
        'SILVERPOP_ID': settings.SILVERPOP_ID,
        'SILVERPOP_BRANDEDDOMAINS': settings.SILVERPOP_BRANDEDDOMAINS,
        'SEO_NOINDEX': settings.SEO_NOINDEX,
        'RCA_LOGIN_DISABLED': settings.RCA_LOGIN_DISABLED,
    }


def navigation_via_api(request):
    if not request.path.startswith(settings.WAGTAIL_ADMIN_URL) and settings.NAVIGATION_API_CONTENT_BASE_URL:
        navigation_api = Navigation()
        return {
            'navigation_via_api_primary': navigation_api.get_primary_navigation(),
            'navigation_via_api_footer_links': navigation_api.get_footer_links(),
            'navigation_via_api_quick_links': navigation_api.get_quick_links(),
            'navigation_via_api_footer_navigation': navigation_api.get_footer_navigation(),
        }
    else:
        return {}