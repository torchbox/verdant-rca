from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from core import models
from verdantsearch import Search, SearchTerms
import json


def search(request):
    query_string = request.GET.get("q", "")
    page = request.GET.get("p", 1)

    # Search
    if query_string != "":
        search_results = models.Page.search_frontend(query_string)

        # Get search terms
        search_terms_obj = SearchTerms.get(query_string)

        # Add hit
        search_terms_obj.add_hit()

        # Pagination
        paginator = Paginator(search_results, 10)
        if paginator is not None:
            try:
                search_results = paginator.page(page)
            except PageNotAnInteger:
                search_results = paginator.page(1)
            except EmptyPage:
                search_results = paginator.page(paginator.num_pages)
        else:
            search_results = None
    else:
        search_terms_obj = None
        search_results = None

    # Render
    if request.is_ajax():
        template_name = getattr(settings, "VERDANTSEARCH_RESULTS_TEMPLATE_AJAX", "verdantsearch/search_results.html")
    else:
        template_name = getattr(settings, "VERDANTSEARCH_RESULTS_TEMPLATE", "verdantsearch/search_results.html")
    return render(request, template_name, dict(query_string=query_string, search_results=search_results, is_ajax=request.is_ajax(), search_terms_obj=search_terms_obj))


def suggest(request):
    query_string = request.GET.get("q", "")

    # Search
    if query_string != "":
        search_results = models.Page.title_search_frontend(query_string)[:5]

        # Get list of suggestions
        suggestions = []
        for result in search_results:
            search_name = result.specific.search_name

            suggestions.append({
                "label": result.title,
                "type": search_name if search_name else '',
                "url": result.url,
            })

        return HttpResponse(json.dumps(suggestions))
    else:
        return HttpResponse("[]")