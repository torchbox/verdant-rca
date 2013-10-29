from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from core import models
from verdantsearch import Search
import json


def search(request):
    query_string = request.GET.get("q", "")
    page = request.GET.get("p", 1)

    # Search
    if query_string != "":
        do_search = True
        search_results = Search().search(query_string, model=models.Page)

        # Pagination
        paginator = Paginator(search_results, 20)
        try:
            search_results =  paginator.page(page)
        except PageNotAnInteger:
            search_results =  paginator.page(1)
        except EmptyPage:
            search_results =  paginator.page(paginator.num_pages)
    else:
        do_search = False
        search_results = None

    # Get template
    template_name = getattr(settings, "VERDANTSEARCH_RESULTS_TEMPLATE", "verdantsearch/search_results.html")

    return render(request, template_name, dict(do_search=do_search, query_string=query_string, search_results=search_results))


def suggest(request):
    query_string = request.GET.get("q", "")

    # Search
    if query_string != "":
        search_results = models.Page.title_search(query_string)[:5]

        # Get list of suggestions
        suggestions = []
        for result in search_results:
            result_specific = result.specific

            suggestions.append({
                "label": str(result_specific.content_type).title() + ": " + result_specific.title,
                "title": result_specific.title,
                "url": result_specific.url,
                "content_type": str(result_specific.content_type).title(),
            })

        return HttpResponse(json.dumps(suggestions))
    else:
        return HttpResponse("[]")