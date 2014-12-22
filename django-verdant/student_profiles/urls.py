"""
New Student Pages, kept as separate URL config for easier enabling/disabling
and for allowing more customization
"""

from django.conf.urls import patterns, url
from .views import basic_profile


urlpatterns = patterns(
    '',

    url(r'^basic/$', basic_profile, name='basic-profile'),
    
)
