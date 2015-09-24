from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from django.contrib import admin
from django.conf import settings
import os.path

from wagtail.wagtailcore import urls as wagtail_urls
from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls

from donations import urls as donations_urls
from rca import app_urls as rca_app_urls, admin_urls as rca_admin_urls
from twitter import urls as twitter_urls
import student_profiles.urls, student_profiles.now_urls

admin.autodiscover()


# Signal handlers
from wagtail.wagtailsearch.signal_handlers import register_signal_handlers as wagtailsearch_register_signal_handlers
wagtailsearch_register_signal_handlers()

from rca_ldap.signal_handlers import register_signal_handlers as rca_ldap_register_signal_handlers
rca_ldap_register_signal_handlers()


urlpatterns = patterns('',
    url(r'^django-admin/', include(admin.site.urls)),
    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),
    url(r'^admin/donations/', include(donations_urls)),
    url(r'^app/', include(rca_app_urls)),
    url(r'^admin/', include(rca_admin_urls)),
    url(r'^twitter/', include(twitter_urls)),

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

    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's serving mechanism
    url(r'', include(wagtail_urls)),
)


if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns() # tell gunicorn where static files are in dev mode
    urlpatterns += static(settings.MEDIA_URL + 'images/', document_root=os.path.join(settings.MEDIA_ROOT, 'images'))
    urlpatterns += patterns('',
        (r'^favicon\.ico$', RedirectView.as_view(url=settings.STATIC_URL + 'rca/images/favicon.ico', permanent=True))
    )
