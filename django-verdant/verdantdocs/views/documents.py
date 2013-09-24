from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from verdantdocs.models import Document
from verdantdocs.forms import DocumentForm
from verdantadmin.forms import SearchForm


def index(request):
    documents = Document.objects.order_by('title')

    return render(request, "verdantdocs/documents/index.html", {
        'documents': documents,
    })


def add(request):
    if request.POST:
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save()
            messages.success(request, "Document '%s' added." % doc.title)
            return redirect('verdantdocs_index')

    else:
        form = DocumentForm()

    return render(request, "verdantdocs/documents/add.html", {
        'form': form,
    })

def search(request):
    if 'q' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            q = form.cleaned_data['q']
            documents = Document.search(q)
    else:
        form = SearchForm()
        documents = Document.objects.order_by('title')

    context = {
        'form': form,
        'documents': documents,
    }
    if request.is_ajax():
        return render(request, "verdantdocs/documents/search-results.html", context)
    else:
        return render(request, "verdantdocs/documents/search.html", context)
