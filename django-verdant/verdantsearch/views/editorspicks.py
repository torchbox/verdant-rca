from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from verdantsearch import models


@login_required
def index(request):
    searchterms_list = models.SearchTerms.objects.all()
    return render(request, 'verdantsearch/editorspicks/index.html', {
        'searchterms_list': searchterms_list
    })


@login_required
def add(request):
    return render(request, 'verdantsearch/editorspicks/add.html', {
    })


@login_required
def edit(request, searchterms_id):
    searchterms = get_object_or_404(models.SearchTerms, pk=searchterms_id)

    return render(request, 'verdantsearch/editorspicks/edit.html', {
        'searchterms': searchterms,
    })

@login_required
def delete(request, searchterms_id):
    searchterms = get_object_or_404(models.SearchTerms, pk=searchterms_id)

    return render(request, 'verdantsearch/editorspicks/confirm_delete.html', {
        'searchterms': searchterms,
    })