"""
New Student Pages, kept as separate URL config for easier enabling/disabling
and for allowing more customization
"""

from django.conf.urls import patterns, url
from .views import overview, basic_profile, academic_details, ma_details, ma_show_details
from .views import image_upload


urlpatterns = patterns(
    '',

    url(r'^$', overview, name='overview'),

    url(r'^new/basic/$', basic_profile, name='new-basic'),

    url(r'^(?P<page_id>\d+)/basic/$', basic_profile, name='edit-basic'),

    url(r'^(?P<page_id>\d+)/academic/$', academic_details, name='edit-academic'),
    url(r'^(?P<page_id>\d+)/ma/$', ma_details, name='edit-ma'),
    url(r'^(?P<page_id>\d+)/ma-show/$', ma_show_details, name='edit-ma-show'),

    url(r'^(?P<page_id>\d+)/basic/image/$', image_upload, {'field': 'profile_image'}, name='edit-basic-image'),
    url(r'^(?P<page_id>\d+)/ma-show/image/$', image_upload, {'field': 'postcard_image'}, name='edit-ma-show-image'),
    
)
