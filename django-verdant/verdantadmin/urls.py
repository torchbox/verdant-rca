from django.conf.urls import patterns, url


urlpatterns = patterns('verdantadmin.views',
    url(r'^$', 'home.home', name='verdantadmin_home'),

    url(r'^pages/$', 'pages.index', name='verdantadmin_explore_root'),
    url(r'^pages/(\d+)/$', 'pages.index', name='verdantadmin_explore'),

    url(r'^pages/new/$', 'pages.select_type', name='verdantadmin_pages_select_type'),
    url(r'^pages/new/(\w+)/(\w+)/$', 'pages.select_location', name='verdantadmin_pages_select_location'),
    url(r'^pages/new/(\w+)/(\w+)/(\d+)/$', 'pages.create', name='verdantadmin_pages_create'),
    url(r'^pages/new/(\w+)/(\w+)/(\d+)/preview/$', 'pages.preview_on_create', name='verdantadmin_pages_preview_on_create'),

    url(r'^pages/(\d+)/edit/$', 'pages.edit', name='verdantadmin_pages_edit'),
    url(r'^pages/(\d+)/edit/preview/$', 'pages.preview_on_edit', name='verdantadmin_pages_preview_on_edit'),

    url(r'^pages/(\d+)/view_draft/$', 'pages.view_draft', name='verdantadmin_pages_view_draft'),
    url(r'^pages/(\d+)/add_subpage/$', 'pages.add_subpage', name='verdantadmin_pages_add_subpage'),
    url(r'^pages/(\d+)/delete/$', 'pages.delete', name='verdantadmin_pages_delete'),
    url(r'^pages/(\d+)/unpublish/$', 'pages.unpublish', name='verdantadmin_pages_unpublish'),

    url(r'^pages/(\d+)/move/$', 'pages.move_choose_destination', name='verdantadmin_pages_move'),
    url(r'^pages/(\d+)/move/(\d+)/$', 'pages.move_choose_destination', name='verdantadmin_pages_move_choose_destination'),
    url(r'^pages/(\d+)/move/(\d+)/confirm/$', 'pages.move_confirm', name='verdantadmin_pages_move_confirm'),

    url(r'^choose-page/$', 'choose_page.browse', name='verdantadmin_choose_page'),
    url(r'^choose-page/(\d+)/$', 'choose_page.browse', name='verdantadmin_choose_page_child'),
    url(r'^choose-external-link/$', 'choose_page.external_link', name='verdantadmin_choose_page_external_link'),
    url(r'^choose-email-link/$', 'choose_page.email_link', name='verdantadmin_choose_page_email_link'),

    url(r'^tag-autocomplete/$', 'tags.autocomplete', name='verdantadmin_tag_autocomplete'),
)
