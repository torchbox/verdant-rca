from django.conf.urls import patterns, url


urlpatterns = patterns('verdantdocs.views',
    url(r'^$', 'documents.index', name='verdantdocs_index'),
)
