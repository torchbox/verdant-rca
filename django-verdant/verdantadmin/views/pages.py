from django.shortcuts import render

from core.models import Page


def index(request):
    pages = Page.objects.order_by('title')
    return render(request, 'verdantadmin/pages/index.html', {
        'pages': pages,
    })
