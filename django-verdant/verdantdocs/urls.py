from django.conf.urls import patterns, url

urlpatterns = patterns('verdantdocs.views',
    url(r'^(\d+)/(.*)$', 'serve.serve', name='verdantdocs_serve'),
)
