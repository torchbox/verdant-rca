from django.conf.urls import patterns, url
from verdantadmin.forms import LoginForm

urlpatterns = patterns('django.contrib.auth.views',
    url(r'^login/$', 'login', {'template_name': 'verdantadmin/login.html', 'authentication_form': LoginForm}),
    url(r'^logout/$', 'logout', {'next_page': '/admin/login/'}),

    # Password reset
    url(r'^password_reset/$', 'password_reset', {
        'template_name': 'verdantadmin/account/password_reset/form.html',
        'email_template_name': 'verdantadmin/account/password_reset/email.txt',
        'subject_template_name': 'verdantadmin/account/password_reset/email_subject.txt',
    }, name='password_reset'),
    url(r'^password_reset/done/$', 'password_reset_done', {'template_name': 'verdantadmin/account/password_reset/done.html'}, name='password_reset_done'),
    url(r'^password_reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        'password_reset_confirm',
        {'template_name': 'verdantadmin/account/password_reset/confirm.html'},
        name='password_reset_confirm',
    ),
    url(r'^password_reset/complete/$', 'password_reset_complete', {'template_name': 'verdantadmin/account/password_reset/complete.html'}, name='password_reset_complete'),
)

urlpatterns += patterns('verdantadmin.views',
    url(r'^$', 'home.home', name='verdantadmin_home'),

    url(r'^failwhale/$', 'home.error_test', name='verdantadmin_error_test'),

    url(r'^pages/$', 'pages.index', name='verdantadmin_explore_root'),
    url(r'^pages/(\d+)/$', 'pages.index', name='verdantadmin_explore'),

    url(r'^pages/new/$', 'pages.select_type', name='verdantadmin_pages_select_type'),
    url(r'^pages/new/(\w+)/(\w+)/$', 'pages.select_location', name='verdantadmin_pages_select_location'),
    url(r'^pages/new/(\w+)/(\w+)/(\d+)/$', 'pages.create', name='verdantadmin_pages_create'),
    url(r'^pages/new/(\w+)/(\w+)/(\d+)/preview/$', 'pages.preview_on_create', name='verdantadmin_pages_preview_on_create'),
    url(r'^pages/usage/(\w+)/(\w+)/$', 'pages.content_type_use', name='verdantadmin_pages_type_use'),

    url(r'^pages/(\d+)/edit/$', 'pages.edit', name='verdantadmin_pages_edit'),
    url(r'^pages/(\d+)/edit/preview/$', 'pages.preview_on_edit', name='verdantadmin_pages_preview_on_edit'),

    url(r'^pages/preview_placeholder/$', 'pages.preview_placeholder', name='verdantadmin_pages_preview_placeholder'),

    url(r'^pages/(\d+)/view_draft/$', 'pages.view_draft', name='verdantadmin_pages_view_draft'),
    url(r'^pages/(\d+)/add_subpage/$', 'pages.add_subpage', name='verdantadmin_pages_add_subpage'),
    url(r'^pages/(\d+)/delete/$', 'pages.delete', name='verdantadmin_pages_delete'),
    url(r'^pages/(\d+)/unpublish/$', 'pages.unpublish', name='verdantadmin_pages_unpublish'),

     url(r'^pages/search/$', 'pages.search', name='verdantadmin_pages_search'),

    url(r'^pages/(\d+)/move/$', 'pages.move_choose_destination', name='verdantadmin_pages_move'),
    url(r'^pages/(\d+)/move/(\d+)/$', 'pages.move_choose_destination', name='verdantadmin_pages_move_choose_destination'),
    url(r'^pages/(\d+)/move/(\d+)/confirm/$', 'pages.move_confirm', name='verdantadmin_pages_move_confirm'),
    url(r'^pages/(\d+)/set_position/$', 'pages.set_page_position', name='verdantadmin_pages_set_page_position'),

    url(r'^pages/moderation/(\d+)/approve/$', 'pages.approve_moderation', name='verdantadmin_pages_approve_moderation'),
    url(r'^pages/moderation/(\d+)/reject/$', 'pages.reject_moderation', name='verdantadmin_pages_reject_moderation'),
    url(r'^pages/moderation/(\d+)/preview/$', 'pages.preview_for_moderation', name='verdantadmin_pages_preview_for_moderation'),

    url(r'^choose-page/$', 'chooser.browse', name='verdantadmin_choose_page'),
    url(r'^choose-page/(\d+)/$', 'chooser.browse', name='verdantadmin_choose_page_child'),
    url(r'^choose-external-link/$', 'chooser.external_link', name='verdantadmin_choose_page_external_link'),
    url(r'^choose-email-link/$', 'chooser.email_link', name='verdantadmin_choose_page_email_link'),

    url(r'^tag-autocomplete/$', 'tags.autocomplete', name='verdantadmin_tag_autocomplete'),

    url(r'^account/$', 'account.account', name='verdantadmin_account'),
    url(r'^account/change_password/$', 'account.change_password', name='verdantadmin_account_change_password'),
)
