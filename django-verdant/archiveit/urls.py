from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^rca-show/$', views.rca_show, name="rca_show"),
)
