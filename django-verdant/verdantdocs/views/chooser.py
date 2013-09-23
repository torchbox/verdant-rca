from django.shortcuts import get_object_or_404

import json

from verdantadmin.modal_workflow import render_modal_workflow
from verdantdocs.models import Document


def chooser(request):
    documents = Document.objects.order_by('title')

    return render_modal_workflow(
        request, 'verdantdocs/chooser/chooser.html', 'verdantdocs/chooser/chooser.js',
        {'documents': documents}
    )


def document_chosen(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    document_json = json.dumps({'id': document.id, 'title': document.title})

    return render_modal_workflow(
        request, None, 'verdantdocs/chooser/document_chosen.js',
        {'document_json': document_json}
    )
