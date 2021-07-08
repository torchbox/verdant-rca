from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from django.contrib import admin
from django.conf import settings
from django.views.decorators.cache import cache_control, never_cache
import os.path

from wagtail.wagtailcore import urls as wagtail_urls
from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls
from wagtail.wagtaildocs.api.v2.endpoints import DocumentsAPIEndpoint
from wagtail.wagtailimages import urls as wagtailimages_urls
from wagtail.utils.urlpatterns import decorate_urlpatterns
from rcasitemaps.views import index, sitemap

from wagtail.api.v2.router import WagtailAPIRouter
from rca.api.endpoints import RCAPagesAPIEndpoint, RCAImagesAPIEndpoint

from archiveit import urls as archiveit_urls
from donations import urls as donations_urls
from rca import admin_urls as rca_admin_urls
from twitter import urls as twitter_urls
import student_profiles.urls, student_profiles.now_urls
from taxonomy import views as taxonomy_views
from rcasitemaps.sitemap_generator import Sitemap
from . import admin_views

from rcasite.cache import get_default_cache_control_decorator

admin.autodiscover()

sitemaps = {'wagtail': Sitemap}

# Signal handlers
from wagtail.wagtailsearch.signal_handlers import register_signal_handlers as wagtailsearch_register_signal_handlers
wagtailsearch_register_signal_handlers()

from rca_ldap.signal_handlers import register_signal_handlers as rca_ldap_register_signal_handlers
rca_ldap_register_signal_handlers()


# Wagtail API
api_router = WagtailAPIRouter('wagtailapi_v2')
api_router.register_endpoint('pages', RCAPagesAPIEndpoint)
api_router.register_endpoint('images', RCAImagesAPIEndpoint)
api_router.register_endpoint('documents', DocumentsAPIEndpoint)


urlpatterns = patterns('',
    # Mitigation for CVE-2020-11001
    # https://github.com/wagtail/wagtail/security/advisories/GHSA-v2wc-pfq2-5cm6
    # This should be properly patched by upgrading to a supported Wagtail version
    url(r'^admin/pages/(\d+)/revisions/compare/', RedirectView.as_view(url='/admin/')),

    url(r'^django-admin/', include(admin.site.urls)),

    # TEMPORARY: Override login view to allow it to be disabled
    url(r'^' + settings.WAGTAIL_ADMIN_URL + 'login/$', admin_views.login),

    url(r'^' + settings.WAGTAIL_ADMIN_URL, include(wagtailadmin_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),
    url(r'^images/', include(wagtailimages_urls)),
    url(r'^' + settings.WAGTAIL_ADMIN_URL + 'donations/', include(donations_urls)),
    url(r'^' + settings.WAGTAIL_ADMIN_URL, include(rca_admin_urls)),
    url(r'^twitter/', include(twitter_urls)),
    url(r'^taxonomy/api/v1/$', never_cache(taxonomy_views.api), name='taxonomy_api_v0'),
    url(r'^api/v2/', include(decorate_urlpatterns(api_router.get_urlpatterns(), never_cache), namespace=api_router.url_namespace)),

    url(r'^search/$', 'wagtail.wagtailsearch.views.search', {
        'template': 'rca/search_results.html',
        'template_ajax': 'rca/includes/search_listing.html',
    }, name='wagtailsearch_search'),
    url(r'^search/suggest/$', 'wagtail.wagtailsearch.views.search', {
        'use_json': True,
        'json_attrs': ['title', 'url', 'search_name', 'search_url']
    }, name='wagtailsearch_suggest'),

    url(r'^my-rca/', include(student_profiles.urls, namespace='student-profiles')),
    url(r'^my-rca/nowpages/', include(student_profiles.now_urls, namespace='nowpages')),

    url(r'^programme_search/', 'rca.views.programme_search', name="programme_search"),

    url(r'^archive-it/', include(archiveit_urls)),

    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's serving mechanism
    url(r'', include(wagtail_urls)),

    url(r'^sitemap\.xml$', index, {'sitemaps': sitemaps}),
    url(r'^sitemap-(?P<section>.+)\.xml$', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

)


if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns() # tell gunicorn where static files are in dev mode
    urlpatterns += static(settings.MEDIA_URL + 'images/', document_root=os.path.join(settings.MEDIA_ROOT, 'images'))
    urlpatterns += patterns('',
        (r'^favicon\.ico$', RedirectView.as_view(url=settings.STATIC_URL + 'rca/images/favicon.ico', permanent=True))
    )


# Set public URLs to use the "default" cache settings.
urlpatterns = decorate_urlpatterns(urlpatterns, get_default_cache_control_decorator())
