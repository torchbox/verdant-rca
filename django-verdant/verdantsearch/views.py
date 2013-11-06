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
        search_results = models.Page.search_frontend(query_string)

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
        search_results = None

    # Render
    if request.is_ajax():
        template_name = getattr(settings, "VERDANTSEARCH_RESULTS_TEMPLATE_AJAX", "verdantsearch/search_results.html")
    else:
        template_name = getattr(settings, "VERDANTSEARCH_RESULTS_TEMPLATE", "verdantsearch/search_results.html")
    return render(request, template_name, dict(query_string=query_string, search_results=search_results, is_ajax=request.is_ajax()))


def suggest(request):
    query_string = request.GET.get("q", "")

    # Search
    if query_string != "":
        search_results = models.Page.title_search_frontend(query_string)[:5]

        # Get list of suggestions
        suggestions = []
        for result in search_results:
            model = result.content_type.model_class()
            if hasattr(model, "search_name"):
                if model.search_name is None:
                    content_type = ""
                else:
                    content_type = " | " + model.search_name
            else:
                content_type = " | " + model.__name__

            suggestions.append({
                "label": result.title + content_type,
                "value": result.title,
                "url": result.url,
            })

        return HttpResponse(json.dumps(suggestions))
    else:
        return HttpResponse("[]")