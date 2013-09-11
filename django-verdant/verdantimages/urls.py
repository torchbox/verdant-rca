from django.conf.urls import patterns, url


urlpatterns = patterns('verdantimages.views',
    url(r'^chooser/$', 'chooser', name='verdantimages_chooser'),
)
