from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^(\d+)/$', views.index, name="index"),
)
