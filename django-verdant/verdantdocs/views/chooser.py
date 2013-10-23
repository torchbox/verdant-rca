from django.shortcuts import get_object_or_404, render

import json

from verdantadmin.modal_workflow import render_modal_workflow
from verdantdocs.models import Document
from verdantdocs.forms import DocumentForm
from verdantadmin.forms import SearchForm


def chooser(request):
    uploadform = DocumentForm()
    documents = []
    if 'q' in request.GET:
        searchform = SearchForm(request.GET)
        if searchform.is_valid():
            q = searchform.cleaned_data['q']
            documents = Document.search(q, prefetch_tags=True)
        return render(request, "verdantdocs/chooser/search_results.html", {'documents': documents})
    else:
        searchform = SearchForm()

    return render_modal_workflow(
        request, 'verdantdocs/chooser/chooser.html', 'verdantdocs/chooser/chooser.js',
        {'documents': documents, 'uploadform': uploadform, 'searchform': searchform,}
    )


def document_chosen(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    document_json = json.dumps({'id': document.id, 'title': document.title})

    return render_modal_workflow(
        request, None, 'verdantdocs/chooser/document_chosen.js',
        {'document_json': document_json}
    )


def chooser_upload(request):
    if request.POST:
        form = DocumentForm(request.POST, request.FILES)

        if form.is_valid():
            document = form.save()
            document_json = json.dumps({'id': document.id, 'title': document.title})
            return render_modal_workflow(
                request, None, 'verdantdocs/chooser/document_chosen.js',
                {'document_json': document_json}
            )
    else:
        form = DocumentForm()

    documents = Document.objects.order_by('title')

    return render_modal_workflow(
        request, 'verdantdocs/chooser/chooser.html', 'verdantdocs/chooser/chooser.js',
        {'documents': documents, 'uploadform': form}
    )
