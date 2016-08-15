from __future__ import absolute_import, unicode_literals

from wagtail.wagtailimages.api.v2.endpoints import ImagesAPIEndpoint

from .serializers import RCAImageSerializer


class RCAImagesAPIEndpoint(ImagesAPIEndpoint):
    base_serializer_class = RCAImageSerializer

    body_fields = ImagesAPIEndpoint.body_fields + [
        'thumbnail',
        'original',
    ]
