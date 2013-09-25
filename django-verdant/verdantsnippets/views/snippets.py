from django.shortcuts import get_object_or_404, render
from django.utils.encoding import force_text

from verdantsnippets.models import SNIPPET_CONTENT_TYPES


def index(request):
    snippet_types = [
        (
            force_text(snippet_type.model_class()._meta.verbose_name_plural),
            snippet_type
        )
        for snippet_type in SNIPPET_CONTENT_TYPES
    ]
    return render(request, 'verdantsnippets/snippets/index.html', {
        'snippet_types': snippet_types,
    })
