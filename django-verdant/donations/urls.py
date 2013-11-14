from django.conf.urls import patterns, url

urlpatterns = patterns('donations.views',
    # url(r'^$', 'donation', name='donation'),
    url(r'^export/$', 'export', name='donations_export'),
    url(r'^dashboard/$', 'verdantadmin', {'title': "Donations"}, name='verdantadmin_tab_donations_dashboard'),
)
