from django.conf.urls import patterns, url


urlpatterns = patterns('verdantadmin.views',
    url(r'^$', 'home.home', name='verdantadmin_home'),
    url(r'^pages/$', 'pages.index', name='verdantadmin_pages_index'),
    url(r'^pages/new/$', 'pages.select_type', name='verdantadmin_pages_select_type'),
    url(r'^pages/(\d+)/$', 'pages.edit', name='verdantadmin_pages_edit'),
)
