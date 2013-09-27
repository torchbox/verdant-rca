from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from verdantdocs.models import Document
from verdantdocs.forms import DocumentForm
from verdantadmin.forms import SearchForm


def index(request):
    documents = Document.objects.order_by('-created_at')[:12]
    form = SearchForm()

    return render(request, "verdantdocs/documents/index.html", {
        'documents': documents,
        'form': form,
        'popular_tags': Document.popular_tags(),
        'is_searching': False,
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


def edit(request, document_id):
    doc = get_object_or_404(Document, id=document_id)
    if request.POST:
        original_file = doc.file
        form = DocumentForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            if 'file' in form.changed_data:
                # if providing a new document file, delete the old one.
                # NB Doing this via original_file.delete() clears the file field,
                # which definitely isn't what we want...
                original_file.storage.delete(original_file.name)
            doc = form.save()
            messages.success(request, "Document '%s' updated." % doc.title)
            return redirect('verdantdocs_index')

    else:
        form = DocumentForm(instance=doc)

    return render(request, "verdantdocs/documents/edit.html", {
        'document': doc,
        'form': form,
    })


def delete(request, document_id):
    doc = get_object_or_404(Document, id=document_id)

    if request.POST:
        doc.delete()
        messages.success(request, "Document '%s' deleted." % doc.title)
        return redirect('verdantdocs_index')

    return render(request, "verdantdocs/documents/confirm_delete.html", {
        'document': doc,
    })


def search(request):
    documents = []
    if 'q' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            q = form.cleaned_data['q']
            documents = Document.search(q)
    else:
        form = SearchForm()

    if request.is_ajax():
        return render(request, "verdantdocs/documents/search-results.html", {
            'documents': documents,
        })
    else:
        return render(request, "verdantdocs/documents/index.html", {
            'form': form,
            'documents': documents,
            'is_searching': True,
            'popular_tags': Document.popular_tags(),
        })
