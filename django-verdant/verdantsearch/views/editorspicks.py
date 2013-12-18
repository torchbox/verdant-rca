from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from verdantsearch import models


@login_required
def index(request):
    searchterms_list = models.SearchTerms.objects.all()
    return render(request, 'verdantsearch/editorspicks/index.html', dict(searchterms_list=searchterms_list))


@login_required
def add(request):
    pass


@login_required
def edit(request, searchterms_id):
    pass


@login_required
def delete(request, searchterms_id):
    pass