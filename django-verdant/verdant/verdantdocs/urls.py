from django.conf.urls import patterns, url

urlpatterns = patterns('verdant.verdantdocs.views',
    url(r'^(\d+)/(.*)$', 'serve.serve', name='verdantdocs_serve'),
)
