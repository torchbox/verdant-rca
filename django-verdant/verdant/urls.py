from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'verdant.views.home', name='home'),
    # url(r'^verdant/', include('verdant.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^admin/', include(admin.site.urls)),

    # For anything not caught by a more specific rule above, hand over to
    # Verdant's serving mechanism. Here we match a (possibly empty) list of
    # path segments, each followed by a '/'. If a trailing slash is not
    # present, we leave CommonMiddleware to handle it as usual (i.e. redirect it
    # to the trailing slash version if settings.APPEND_SLASH is True)
    url(r'^((?:\w+/)*)$', 'core.views.serve' )
)
