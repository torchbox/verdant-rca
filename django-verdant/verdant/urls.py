from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings
import os.path

from core import urls as verdant_urls
from verdantadmin import urls as verdantadmin_urls
from verdantimages import urls as verdantimages_urls
from verdantdocs import admin_urls as verdantdocs_admin_urls
from verdantdocs import urls as verdantdocs_urls
from verdantsnippets import urls as verdantsnippets_urls

from rca import app_urls

admin.autodiscover()

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
    url(r'^admin/documents/', include(verdantdocs_admin_urls)),
    url(r'^admin/snippets/', include(verdantsnippets_urls)),
    url(r'^admin/', include(verdantadmin_urls)),

    url(r'^documents/', include(verdantdocs_urls)),

    url(r'^app/', include(app_urls)),

    # For anything not caught by a more specific rule above, hand over to
    # Verdant's serving mechanism
    url(r'', include(verdant_urls))
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL + 'images/', document_root=os.path.join(settings.MEDIA_ROOT, 'images'))
