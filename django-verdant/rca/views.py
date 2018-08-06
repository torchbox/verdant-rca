"""
Views defined here are global ones that live at a fixed URL (defined in rca/app_urls.py)
unrelated to the site tree structure. Typically this would be used for things like content
pulled in via AJAX.
"""
from django.http import JsonResponse

from rca.models import ProgrammePage


def programme_search(request):
    q = request.GET.get('q')

    if q:
        programmes = ProgrammePage.objects.exclude(exclude_from_programme_finder=True).live().public()
        programmes = [
            {
                'title': p.title,
                'url': p.url
            }
            for p in programmes.filter(title__icontains=q)
        ]
    else:
        programmes = []

    return JsonResponse(programmes, safe=False)
