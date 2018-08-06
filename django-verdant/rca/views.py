"""
Views defined here are global ones that live at a fixed URL (defined in rca/app_urls.py)
unrelated to the site tree structure. Typically this would be used for things like content
pulled in via AJAX.
"""
from django.db.models import Q
from django.http import JsonResponse


from rca.models import ProgrammePage


def programme_search(request):
    q = request.GET.get('q')

    if q:
        programme_query = ProgrammePage.objects \
            .exclude(programme_finder_exclude=True).live().public() \
            .filter(Q(title__icontains=q) | Q(programme_finder_keywords__name__icontains=q)) \
            .order_by('title').distinct('title')

        programmes = [
            {
                'title': p.title,
                'url': p.url
            }
            for p in programme_query
        ]
    else:
        programmes = []

    return JsonResponse(programmes, safe=False)
