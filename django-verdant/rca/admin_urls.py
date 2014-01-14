# RCA-specific extensions to Verdant admin.

from django.conf.urls import patterns, url


urlpatterns = patterns('rca.admin_views',
    url(r'^rcanow/$', 'rca_now_index', name='rca_now_editor_index'),
)
