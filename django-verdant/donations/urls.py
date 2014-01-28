from django.conf.urls import patterns, url

urlpatterns = patterns('donations.views',
    # url(r'^$', 'donation', name='donation'),
    url(r'^export/gift-aid-only/$', 'export', name='donations_export'),
    url(r'^export/all/$', 'export', {'include_all': True}, name='donations_export_all'),
    url(r'^dashboard/$', 'wagtailadmin', {'title': "Donations"}, name='wagtailadmin_tab_donations_dashboard'),
)
