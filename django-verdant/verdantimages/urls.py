from django.conf.urls import patterns, url


urlpatterns = patterns('verdantimages.views',
    url(r'^chooser/$', 'chooser', name='verdantimages_chooser'),
    url(r'^chooser/(\d+)/$', 'image_chosen', name='verdantimages_image_chosen'),
    url(r'^chooser/upload/$', 'chooser_upload', name='verdantimages_chooser_upload'),
)
