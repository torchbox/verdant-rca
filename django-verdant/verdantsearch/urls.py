from django.conf.urls import patterns, url


urlpatterns = patterns('verdantadmin.views',
    url(r"^$", "views.search", name="verdantsearch_search"),
    url(r"^suggest/$", "views.suggest", name="verdantsearch_suggest"),
)
