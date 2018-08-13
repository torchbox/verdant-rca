"""
Views defined here are global ones that live at a fixed URL (defined in rca/app_urls.py)
unrelated to the site tree structure. Typically this would be used for things like content
pulled in via AJAX.
"""
from collections import OrderedDict

from django.db.models import Q
from django.http import JsonResponse

from wagtail.wagtailcore.query import PageQuerySet
from wagtail.wagtailimages.models import SourceImageIOError

from rca.models import ProgrammePage
from shortcourses.models import ShortCoursePage


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
    except AttributeError:
        return ''


def map_programme_search_fields(pages, root_url):
    return [
        {
            'title': p.title,
            'url': p.url,
            'thumbnail': get_image_detail(p.feed_image, 'max-165x165', root_url)
        }
        for p in pages
    ]


def programme_search(request):
    """ Programme finder search function. """
    q = request.GET.get('q')

    if q:
        pqs = PageQuerySet()

        query = Q(
            Q(title__icontains=q) | Q(programme_finder_keywords__name__icontains=q),
            ~Q(programme_finder_exclude=True),
            pqs.live_q(),
            pqs.public_q(),
        )

        courses = map_programme_search_fields(
            ProgrammePage.objects.filter(query).order_by('title').distinct('title'),
            request.site.root_url
        )

        courses.extend(map_programme_search_fields(
            ShortCoursePage.objects.filter(query).order_by('title').distinct('title'),
            request.site.root_url
        ))

        courses.sort(key=lambda c: c['title'])
    else:
        courses = []

    return JsonResponse(courses, safe=False)
