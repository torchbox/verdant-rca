from django.conf.urls import patterns, url


urlpatterns = patterns('verdantadmin.views',
    url(r'^$', 'home.home', name='verdantadmin_home'),

    url(r'^pages/$', 'pages.index', name='verdantadmin_explore_root'),
    url(r'^pages/(\d+)/$', 'pages.index', name='verdantadmin_explore'),

    url(r'^pages/new/$', 'pages.select_type', name='verdantadmin_pages_select_type'),
    url(r'^pages/new/(\w+)/(\w+)/$', 'pages.select_location', name='verdantadmin_pages_select_location'),
    url(r'^pages/new/(\w+)/(\w+)/(\d+)/$', 'pages.create', name='verdantadmin_pages_create'),
    url(r'^pages/(\d+)/edit/$', 'pages.edit', name='verdantadmin_pages_edit'),

    url(r'^pages/(\d+)/add_subpage/$', 'pages.add_subpage', name='verdantadmin_pages_add_subpage'),

    url(r'^choose-page/(\w+)/(\w+)/$', 'choose_page.browse', name='verdantadmin_choose_page'),
    url(r'^choose-page/(\w+)/(\w+)/(\d+)/$', 'choose_page.browse', name='verdantadmin_choose_page_child'),
)
