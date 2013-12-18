from django.conf.urls import patterns, url


urlpatterns = patterns("verdantsearch.views.frontend",
    url(r"^$", "search", name="verdantsearch_search"),
    url(r"^suggest/$", "suggest", name="verdantsearch_suggest"),
)
