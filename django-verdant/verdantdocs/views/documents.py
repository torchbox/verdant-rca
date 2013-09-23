from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from verdantdocs.models import Document

def index(request):
    documents = Document.objects.order_by('title')

    return render(request, "verdantdocs/documents/index.html", {
        'documents': documents,
    })
