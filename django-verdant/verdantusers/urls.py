from django.conf.urls import patterns, url

urlpatterns = patterns('verdantusers.views',
    url(r'^$', 'users.index', name='verdantusers_index'),
    url(r'^new/$', 'users.create', name='verdantusers_create'),
    url(r'^logintest/$', 'users.logintest', name='verdantusers_logintest'),
)
