from django.shortcuts import get_object_or_404, render
from wagtail.wagtailcore.models import Page


def index(request, parent_page_id):
    parent = get_object_or_404(Page, pk=parent_page_id)
    pages = parent.get_children().live().public()
    return render(request, 'rca/archive_it.html', {
        'count': pages.count(),
        'pages': pages,
        'parent': parent,
    })
