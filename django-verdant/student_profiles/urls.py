"""
New Student Pages, kept as separate URL config for easier enabling/disabling
and for allowing more customization
"""

from django.conf.urls import patterns, url
from .views import overview, basic_profile, academic_details, ma_details, ma_show_details


urlpatterns = patterns(
    '',

    url(r'^$', overview, name='overview'),

    url(r'^new/basic/$', basic_profile, name='new-basic'),
    url(r'^(?P<page_id>\d+)/basic/$', basic_profile, name='edit-basic'),
    url(r'^(?P<page_id>\d+)/academic/$', academic_details, name='edit-academic'),
    url(r'^(?P<page_id>\d+)/ma/$', ma_details, name='edit-ma'),
    url(r'^(?P<page_id>\d+)/ma-show/$', ma_show_details, name='edit-ma-show'),
    
)
