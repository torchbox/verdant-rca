from django.conf.urls import patterns, url


urlpatterns = patterns('verdantimages.views',
    url(r'^$', 'images.index', name='verdantimages_index'),
    url(r'^(\d+)/$', 'images.edit', name='verdantimages_edit_image'),
    url(r'^(\d+)/delete/$', 'images.delete', name='verdantimages_delete_image'),
    url(r'^add/$', 'images.add', name='verdantimages_add_image'),
    url(r'^search/$', 'images.search', name='verdantimages_search_image'),

    url(r'^chooser/$', 'chooser.chooser', name='verdantimages_chooser'),
    url(r'^chooser/(\d+)/$', 'chooser.image_chosen', name='verdantimages_image_chosen'),
    url(r'^chooser/upload/$', 'chooser.chooser_upload', name='verdantimages_chooser_upload'),
    url(r'^chooser/(\d+)/select_format/$', 'chooser.chooser_select_format', name='verdantimages_chooser_select_format'),
)
