"""
Views defined here are global ones that live at a fixed URL (defined in rca/app_urls.py)
unrelated to the site tree structure. Typically this would be used for things like content
pulled in via AJAX.
"""
from collections import OrderedDict

from django.db.models import Q
from django.http import JsonResponse

from wagtail.wagtailimages.models import SourceImageIOError

from rca.models import ProgrammePage


def get_image_detail(image, filter_spec, root_url):
    """ Return the rendition info the given info, spec and site URL. """
    try:
        thumbnail = image.get_rendition(filter_spec)

        return OrderedDict([
            ('url', root_url + thumbnail.url),
            ('width', thumbnail.width),
            ('height', thumbnail.height),
        ])
    except SourceImageIOError:
        return OrderedDict([
            ('error', 'SourceImageIOError'),
        ])


def programme_search(request):
    """ Programme finder search function. """
    q = request.GET.get('q')

    if q:
        programme_query = ProgrammePage.objects.live().public() \
            .exclude(programme_finder_exclude=True) \
            .filter(Q(title__icontains=q) | Q(programme_finder_keywords__name__icontains=q)) \
            .order_by('title').distinct('title')

        programmes = [
            {
                'title': p.title,
                'url': p.url,
                'thumbnail': get_image_detail(p.feed_image, 'max-165x165', request.site.root_url)
            }
            for p in programme_query
        ]
    else:
        programmes = []

    return JsonResponse(programmes, safe=False)
