from __future__ import absolute_import, unicode_literals

from wagtail.api.v2.endpoints import PagesAPIEndpoint
from wagtail.wagtailimages.api.v2.endpoints import ImagesAPIEndpoint

from .serializers import RCAPageSerializer, RCAImageSerializer
from .filters import RelatedProgrammesFilter, NextEventOrder, NegatedTagFilter


class RCAPagesAPIEndpoint(PagesAPIEndpoint):
    base_serializer_class = RCAPageSerializer

    meta_fields = PagesAPIEndpoint.meta_fields + [
        'children',
        'descendants',
        'parent',
        'ancestors',
    ]

    listing_default_fields = PagesAPIEndpoint.listing_default_fields + [
        'children',
    ]

    # Allow the parent field to appear on listings
    detail_only_fields = []

    filter_backends = [
        RelatedProgrammesFilter,
        NextEventOrder,
        NegatedTagFilter,
    ] + PagesAPIEndpoint.filter_backends
    known_query_parameters = PagesAPIEndpoint.known_query_parameters.union([
        'rp',
        'event_date_from',
        'tags_not',
    ])


class RCAImagesAPIEndpoint(ImagesAPIEndpoint):
    base_serializer_class = RCAImageSerializer

    body_fields = ImagesAPIEndpoint.body_fields + [
        'thumbnail',
        'original',
        'rca2019_feed_image',
        'rca2019_feed_image_small',
    ]
