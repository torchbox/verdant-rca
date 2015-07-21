"""
RCA Now blog posts, kept as separate URL config for easier enabling/disabling
and for allowing more customization
"""

from django.conf.urls import patterns, url

from .now_views import overview, edit, preview, submit, delete
from .now_views import image_upload

urlpatterns = patterns(
    '',

    url(r'^$', overview, name='overview'),
    url(r'^(?P<page_id>\d+)/preview/$', preview, name='preview'),
    url(r'^(?P<page_id>\d+)/submit/$', submit, name='submit'),

    url(r'^new/$', edit, name='create'),

    url(r'^(?P<page_id>\d+)/edit/$', edit, name='edit'),
    url(r'^(?P<page_id>\d+)/delete/$', delete, name='delete'),

    url(r'^(?P<page_id>\d+)/edit/image/$', image_upload),
)
