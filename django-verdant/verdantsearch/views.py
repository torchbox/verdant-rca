from django.conf import settings
from django.shortcuts import render
from core import models


def search(request):
    query_string = request.GET.get("q", "")

    # Search
    if query_string != "":
        do_search = True
        search_results = models.Page.title_search(query_string)
    else:
        do_search = False
        search_results = None

    # Get template
    template_name = getattr(settings, "VERDANTSEARCH_RESULTS_TEMPLATE", "verdantsearch/search_results.html")

    return render(request, template_name, dict(do_search=do_search, query_string=query_string, search_results=search_results))


def suggest(request):
    query_string = request.GET.get("q", "")
