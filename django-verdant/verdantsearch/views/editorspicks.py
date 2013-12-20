from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from verdantsearch import models


@login_required
def index(request):
    # Select only search terms with editors picks
    searchterms_list = models.SearchTerms.objects.filter(editors_picks__isnull=False).distinct()
    return render(request, 'verdantsearch/editorspicks/index.html', {
        'searchterms_list': searchterms_list,
    })


@login_required
def add(request):
    return render(request, 'verdantsearch/editorspicks/add.html', {
    })


@login_required
def edit(request, searchterms_urlified):
    searchterms_terms = models.SearchTerms._deurlify_terms(searchterms_urlified)
    searchterms = get_object_or_404(models.SearchTerms, terms=searchterms_terms)

    return render(request, 'verdantsearch/editorspicks/edit.html', {
        'searchterms': searchterms,
    })