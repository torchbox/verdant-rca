"""
New Student Pages, kept as separate URL config for easier enabling/disabling
and for allowing more customization
"""

from django.conf.urls import patterns, url
from .views import overview, basic_profile


urlpatterns = patterns(
    '',

    url(r'^$', overview, name='overview'),

    url(r'^new/basic/$', basic_profile, name='new-basic'),
    url(r'^(?P<page_id>\d+)/basic/$', basic_profile, name='edit-basic'),
    
)
