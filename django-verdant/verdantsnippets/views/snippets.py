from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.encoding import force_text
from django.utils.text import capfirst
from django.contrib.contenttypes.models import ContentType

from verdantsnippets.models import SNIPPET_CONTENT_TYPES


def get_snippet_type_name(content_type):
    """ e.g. given the 'advert' content type, return "Adverts" """
    # why oh why is this so convoluted?
    verbose_name_plural = content_type.model_class()._meta.verbose_name_plural
    return capfirst(force_text(verbose_name_plural))

def index(request):
    snippet_types = [
        (
            get_snippet_type_name(content_type),
            content_type
        )
        for content_type in SNIPPET_CONTENT_TYPES
    ]
    return render(request, 'verdantsnippets/snippets/index.html', {
        'snippet_types': snippet_types,
    })


def list(request, content_type_app_name, content_type_model_name):
    try:
        content_type = ContentType.objects.get_by_natural_key(content_type_app_name, content_type_model_name)
    except ContentType.DoesNotExist:
        raise Http404
    if content_type not in SNIPPET_CONTENT_TYPES:
        # don't allow people to hack the URL to edit content types that aren't registered as snippets
        raise Http404

    model = content_type.model_class()

    items = model.objects.all()

    return render(request, 'verdantsnippets/snippets/list.html', {
        'content_type': content_type,
        'snippet_type_name': get_snippet_type_name(content_type),
        'items': items,
    })
