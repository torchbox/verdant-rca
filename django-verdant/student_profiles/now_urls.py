"""
RCA Now blog posts, kept as separate URL config for easier enabling/disabling
and for allowing more customization
"""

from django.conf.urls import patterns, url

from .now_views import overview, create, edit, preview, submit

urlpatterns = patterns(
    '',

    url(r'^$', overview, name='overview'),
    url(r'^(?P<page_id>\d+)/preview/$', preview, name='preview'),
    url(r'^(?P<page_id>\d+)/submit/$', submit, name='submit'),

    url(r'^new/$', create, name='create'),

    url(r'^(?P<page_id>\d+)/edit/$', edit, name='edit'),

)
