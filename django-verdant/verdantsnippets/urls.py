from django.conf.urls import patterns, url


urlpatterns = patterns('verdantsnippets.views',
    url(r'^$', 'snippets.index', name='verdantsnippets_index'),
    url(r'^(\w+)/(\w+)/$', 'snippets.list', name='verdantsnippets_list'),
)
