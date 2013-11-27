from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from django.contrib import admin
from django.conf import settings
import os.path

from core import urls as verdant_urls
from verdant.verdantadmin import urls as verdantadmin_urls
from verdant.verdantimages import urls as verdantimages_urls
from verdantmedia import urls as verdantmedia_urls
from verdant.verdantdocs import admin_urls as verdantdocs_admin_urls
from verdant.verdantdocs import urls as verdantdocs_urls
from verdant.verdantsnippets import urls as verdantsnippets_urls
from verdantsearch import urls as verdantsearch_urls
from verdantusers import urls as verdantusers_urls
from verdantredirects import urls as verdantredirects_urls

from donations import urls as donations_urls
from rca import app_urls
from twitter import urls as twitter_urls

admin.autodiscover()

from verdantsearch import register_signal_handlers
register_signal_handlers()


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'verdant.views.home', name='home'),
    # url(r'^verdant/', include('verdant.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^django-admin/', include(admin.site.urls)),

    # TODO: some way of getting verdantimages to register itself within verdant so that we
    # don't have to define it separately here
    url(r'^admin/images/', include(verdantimages_urls)),
    url(r'^admin/media/', include(verdantmedia_urls)),
    url(r'^admin/documents/', include(verdantdocs_admin_urls)),
    url(r'^admin/snippets/', include(verdantsnippets_urls)),
    url(r'^admin/users/', include(verdantusers_urls)),
    url(r'^admin/redirects/', include(verdantredirects_urls)),
    url(r'^admin/', include(verdantadmin_urls)),
    url(r'^search/', include(verdantsearch_urls)),

    url(r'^documents/', include(verdantdocs_urls)),

    url(r'^donations/', include(donations_urls)),

    url(r'^app/', include(app_urls)),

    url(r'^twitter/', include(twitter_urls)),

    # For anything not caught by a more specific rule above, hand over to
    # Verdant's serving mechanism
    url(r'', include(verdant_urls)),
)


if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns() # tell gunicorn where static files are in dev mode
    urlpatterns += static(settings.MEDIA_URL + 'images/', document_root=os.path.join(settings.MEDIA_ROOT, 'images'))
    urlpatterns += patterns('',
        (r'^favicon\.ico$', RedirectView.as_view(url=settings.STATIC_URL + 'rca/images/favicon.ico'))
    )
