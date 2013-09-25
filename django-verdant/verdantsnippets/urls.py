from django.conf.urls import patterns, url


urlpatterns = patterns('verdantsnippets.views',
    url(r'^$', 'snippets.index', name='verdantsnippets_index'),
)
