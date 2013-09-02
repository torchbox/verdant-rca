from django.conf.urls import patterns, url


urlpatterns = patterns('verdantadmin.views',
    url(r'^$', 'home.home', name='verdantadmin_home'),
    url(r'^pages/$', 'pages.index', name='verdantadmin_pages_index'),
)
