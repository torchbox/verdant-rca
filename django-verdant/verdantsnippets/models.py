from django.db import models
from django.contrib.contenttypes.models import ContentType

SNIPPET_CONTENT_TYPES = []

def register_snippet(model):
    content_type = ContentType.objects.get_for_model(model)
    if content_type not in SNIPPET_CONTENT_TYPES:
        SNIPPET_CONTENT_TYPES.append(content_type)
