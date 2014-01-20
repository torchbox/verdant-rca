# RCA-specific extensions to Verdant admin.

from django.conf.urls import patterns, url


urlpatterns = patterns('rca.admin_views',
    url(r'^rca_now/$', 'rca_now_index', name='rca_now_editor_index'),
    url(r'^student_page/$', 'student_page_index', name='student_page_editor_index'),
)
