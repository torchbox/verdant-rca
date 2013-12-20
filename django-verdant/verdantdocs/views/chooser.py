from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required

import json

from verdantadmin.modal_workflow import render_modal_workflow
from verdantdocs.models import Document
from verdantdocs.forms import DocumentForm
from verdantadmin.forms import SearchForm


@login_required
def chooser(request):
    uploadform = DocumentForm()
    documents = []
    
    q = None
    is_searching = False
    if 'q' in request.GET or 'p' in request.GET:
        searchform = SearchForm(request.GET)
        if searchform.is_valid():
            q = searchform.cleaned_data['q']

            # page number
            p = request.GET.get("p", 1)

            documents = Document.search(q, results_per_page=10, prefetch_tags=True)
            
            is_searching = True

        else:
            documents = Document.objects.order_by('-created_at')
            
            p = request.GET.get("p", 1)
            paginator = Paginator(documents, 10)

            try:
                documents = paginator.page(p)
            except PageNotAnInteger:
                documents = paginator.page(1)
            except EmptyPage:
                documents = paginator.page(paginator.num_pages)
            
            is_searching = False

        return render(request, "verdantdocs/chooser/results.html", {
            'documents': documents,
            'search_query': q,
            'is_searching': is_searching,
        })
    else:
        searchform = SearchForm()

        documents = Document.objects.order_by('-created_at')
        p = request.GET.get("p", 1)
        paginator = Paginator(documents, 10)

        try:
            documents = paginator.page(p)
        except PageNotAnInteger:
            documents = paginator.page(1)
        except EmptyPage:
            documents = paginator.page(paginator.num_pages)

    return render_modal_workflow(request, 'verdantdocs/chooser/chooser.html', 'verdantdocs/chooser/chooser.js', {
        'documents': documents, 
        'uploadform': uploadform, 
        'searchform': searchform,
        'is_searching': False,
    })


@login_required
def document_chosen(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    document_json = json.dumps({'id': document.id, 'title': document.title})

    return render_modal_workflow(
        request, None, 'verdantdocs/chooser/document_chosen.js',
        {'document_json': document_json}
    )


@login_required
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
