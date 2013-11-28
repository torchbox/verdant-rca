from django.conf.urls import patterns, url


urlpatterns = patterns('verdant.verdantredirects.views',
    url(r'^$', 'index', name='verdantredirects_index'),
    url(r'^(\d+)/$', 'edit', name='verdantredirects_edit_redirect'),
    url(r'^(\d+)/delete/$', 'delete', name='verdantredirects_delete_redirect'),
    url(r'^add/$', 'add', name='verdantredirects_add_redirect'),
)
