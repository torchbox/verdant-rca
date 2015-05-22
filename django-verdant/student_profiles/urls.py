"""
New Student Pages, kept as separate URL config for easier enabling/disabling
and for allowing more customization
"""

from django.conf.urls import patterns, url
from .views import overview, preview, postcard_upload, mphil_show_details, phd_show_details
from .views import disambiguate
from .views import basic_profile, academic_details, ma_details, ma_show_details
from .views import mphil_details, phd_details
from .views import image_upload
from .auth import login, logout

urlpatterns = patterns(
    '',

    url(r'^$', overview, name='overview'),
    url(r'^(?P<page_id>\d+)/$', overview, name='overview-specific'),
    url(r'^disambiguate/$', disambiguate, name='disambiguate'),
    url(r'^(?P<page_id>\d+)/preview/$', preview, name='preview'),

    url(r'^(?P<page_id>\d+)/basic/$', basic_profile, name='edit-basic'),
    url(r'^(?P<page_id>\d+)/cv/$', academic_details, name='edit-academic'),
    url(r'^(?P<page_id>\d+)/postcard/$', postcard_upload, name='edit-postcard'),

    url(r'^(?P<page_id>\d+)/ma/$', ma_details, name='edit-ma'),
    url(r'^(?P<page_id>\d+)/ma-show/$', ma_show_details, name='edit-ma-show'),

    url(r'^(?P<page_id>\d+)/mphil/$', mphil_details, name='edit-mphil'),
    url(r'^(?P<page_id>\d+)/mphil_show/$', mphil_show_details, name='edit-mphil-show'),
    url(r'^(?P<page_id>\d+)/phd/$', phd_details, name='edit-phd'),
    url(r'^(?P<page_id>\d+)/phd_show/$', phd_show_details, name='edit-phd-show'),

    url(r'^(?P<page_id>\d+)/basic/image/$', image_upload, {'field': 'profile_image'}, name='edit-basic-image'),
    url(r'^(?P<page_id>\d+)/postcard/image/$', image_upload, {'field': 'postcard_image', 'max_size': 10 * 1024 * 1024, 'min_dim': (1278, 1795)}),
    url(r'^(?P<page_id>\d+)/ma-show/image/$', image_upload),
    url(r'^(?P<page_id>\d+)/phd_show/image/$', image_upload),
    url(r'^(?P<page_id>\d+)/mphil_show/image/$', image_upload),

    url(r'^login/$', login, name='login'),
    url(r'^logout/$', logout, name='logout'),

)
