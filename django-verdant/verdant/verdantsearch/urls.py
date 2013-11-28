from django.conf.urls import patterns, url


urlpatterns = patterns("verdant.verdantsearch.views",
    url(r"^$", "search", name="verdantsearch_search"),
    url(r"^suggest/$", "suggest", name="verdantsearch_suggest"),
)
