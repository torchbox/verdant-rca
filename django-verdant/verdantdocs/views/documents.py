from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required

from verdantdocs.models import Document
from verdantdocs.forms import DocumentForm
from verdantadmin.forms import SearchForm


@login_required
def index(request):

    q = None
    p = request.GET.get("p", 1)
    is_searching = False
    
    if 'q' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            q = form.cleaned_data['q']

            is_searching = True
            documents = Document.search(q, results_per_page=20, page=p)
        else:
            documents = Document.objects.order_by('-created_at')
    else:
        documents = Document.objects.order_by('-created_at')
        form = SearchForm()

    if not is_searching:
        paginator = Paginator(documents, 20)

        try:
            documents = paginator.page(p)
        except PageNotAnInteger:
            documents = paginator.page(1)
        except EmptyPage:
            documents = paginator.page(paginator.num_pages)

    if request.is_ajax():
        return render(request, "verdantdocs/documents/results.html", {
            'documents': documents,
            'is_searching': is_searching,
            'search_query': q,
        })
    else:
        return render(request, "verdantdocs/documents/index.html", {
            'form': form,
            'documents': documents,
            'popular_tags': Document.popular_tags(),
            'is_searching': is_searching,
            'search_query': q,
        })


@login_required
def add(request):
    if request.POST:
        doc = Document(uploaded_by_user=request.user)
        form = DocumentForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            form.save()
            messages.success(request, "Document '%s' added." % doc.title)
            return redirect('verdantdocs_index')
        else:
            messages.error(request, "The document could not be saved due to errors.")
    else:
        form = DocumentForm()

    return render(request, "verdantdocs/documents/add.html", {
        'form': form,
    })


@login_required
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
            messages.success(request, "Document '%s' updated" % doc.title)
            return redirect('verdantdocs_index')
        else:
            messages.error(request, "The document could not be saved due to errors.")
    else:
        form = DocumentForm(instance=doc)

    return render(request, "verdantdocs/documents/edit.html", {
        'document': doc,
        'form': form,
    })


@login_required
def delete(request, document_id):
    doc = get_object_or_404(Document, id=document_id)

    if request.POST:
        doc.delete()
        messages.success(request, "Document '%s' deleted." % doc.title)
        return redirect('verdantdocs_index')

    return render(request, "verdantdocs/documents/confirm_delete.html", {
        'document': doc,
    })


@login_required
def search(request):
    documents = []
    q = None
    is_searching = False

    if 'q' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            q = form.cleaned_data['q']

            is_searching = True
            documents = Document.search(q, results_per_page=20, prefetch_tags=True)
    else:
        form = SearchForm()

    if request.is_ajax():
        return render(request, "verdantdocs/documents/results.html", {
            'documents': documents,
            'is_searching': is_searching,
            'search_query': q
        })
    else:
        return render(request, "verdantdocs/documents/index.html", {
            'form': form,
            'documents': documents,
            'is_searching': True,
            'search_query': q,
            'popular_tags': Document.popular_tags(),
        })
