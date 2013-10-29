from django.conf.urls import patterns, url

urlpatterns = patterns('verdantusers.views',
    url(r'^logintest/$', 'users.logintest', name='verdantusers_logintest'),
)
