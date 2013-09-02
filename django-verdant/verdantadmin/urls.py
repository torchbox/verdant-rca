from django.conf.urls import patterns, url


urlpatterns = patterns('verdantadmin.views',
    url(r'^$', 'home', name='verdantadmin_home'),
)
