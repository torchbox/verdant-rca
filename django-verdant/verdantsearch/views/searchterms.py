from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required

from verdantadmin.modal_workflow import render_modal_workflow
from verdantadmin.forms import SearchForm
from verdantsearch import models


@login_required
def chooser(request, get_results=False):
    # Get most popular search terms
    searchterms_list = models.SearchTerms.get_most_popular()

    # If searching, filter results by search terms
    if 'q' in request.GET:
        searchform = SearchForm(request.GET)
        if searchform.is_valid():
            q = searchform.cleaned_data['q']
            searchterms_list = searchterms_list.filter(terms__icontains=models.SearchTerms.normalise_terms(q))
            is_searching = True
        else:
            is_searching = False
    else:
        searchform = SearchForm()
        is_searching = False

    # Pagination
    p = request.GET.get('p', 1)

    paginator = Paginator(searchterms_list, 10)
    try:
        searchterms_list = paginator.page(p)
    except PageNotAnInteger:
        searchterms_list = paginator.page(1)
    except EmptyPage:
        searchterms_list = paginator.page(paginator.num_pages)

    # Render
    if get_results:
        return render(request, "verdantsearch/searchterms/chooser/results.html", {
            'searchterms_list': searchterms_list, 
            'is_searching': is_searching,
        })
    else:
        return render_modal_workflow(request, 'verdantsearch/searchterms/chooser/chooser.html', 'verdantsearch/searchterms/chooser/chooser.js',{
            'searchterms_list': searchterms_list,
            'searchform': searchform,
            'is_searching': False,
        })

def chooserresults(request):
    return chooser(request, get_results=True)