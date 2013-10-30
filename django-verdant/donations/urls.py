from django.conf.urls import patterns, url

urlpatterns = patterns('donations.views',
    url(r'^$', 'donation', name='donation'),
)
