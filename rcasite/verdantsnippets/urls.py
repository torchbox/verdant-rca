from django.conf.urls import patterns, url


urlpatterns = patterns('verdantsnippets.views',
    url(r'^$', 'snippets.index', name='verdantsnippets_index'),

    url(r'^choose/(\w+)/(\w+)/$', 'chooser.choose', name='verdantsnippets_choose'),
    url(r'^choose/(\w+)/(\w+)/(\d+)/$', 'chooser.chosen', name='verdantsnippets_chosen'),

    url(r'^(\w+)/(\w+)/$', 'snippets.list', name='verdantsnippets_list'),
    url(r'^(\w+)/(\w+)/new/$', 'snippets.create', name='verdantsnippets_create'),
    url(r'^(\w+)/(\w+)/(\d+)/$', 'snippets.edit', name='verdantsnippets_edit'),
    url(r'^(\w+)/(\w+)/(\d+)/delete/$', 'snippets.delete', name='verdantsnippets_delete'),
)
