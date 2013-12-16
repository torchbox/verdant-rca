from django.conf.urls import patterns, url


urlpatterns = patterns('verdantembeds.views',
    url(r'^chooser/$', 'chooser.chooser', name='verdantembeds_chooser'),
    url(r'^chooser/upload/$', 'chooser.chooser_upload', name='verdantembeds_chooser_upload'),
)
