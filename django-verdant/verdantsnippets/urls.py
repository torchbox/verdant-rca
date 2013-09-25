from django.conf.urls import patterns, url


urlpatterns = patterns('verdantsnippets.views',
    url(r'^$', 'snippets.index', name='verdantsnippets_index'),
    url(r'^(\w+)/(\w+)/$', 'snippets.list', name='verdantsnippets_list'),
    url(r'^(\w+)/(\w+)/new/$', 'snippets.create', name='verdantsnippets_create'),
    url(r'^(\w+)/(\w+)/(\d+)/$', 'snippets.edit', name='verdantsnippets_edit'),
)
