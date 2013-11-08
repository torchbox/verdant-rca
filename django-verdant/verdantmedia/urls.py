from django.conf.urls import patterns, url


urlpatterns = patterns('verdantmedia.views',
    url(r'^chooser/$', 'chooser.chooser', name='verdantmedia_chooser'),
)
