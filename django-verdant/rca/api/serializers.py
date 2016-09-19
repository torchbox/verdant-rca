from __future__ import absolute_import, unicode_literals

from collections import OrderedDict

from rest_framework.fields import Field

from wagtail.wagtailimages.models import SourceImageIOError
from wagtail.wagtailimages.api.v2.serializers import ImageSerializer


class ImageRenditionField(Field):
    """
    A field that generates a rendition with the specified filter spec, and serialises
    details of that rendition.

    Example:
    "thumbnail": {
        "url": "http://rca.ac.uk/media/images/myimage.max-165x165.jpg",
        "width": 165,
        "height": 100
    }

    If there is an error with the source image. The dict will only contain a single
    key, "error", indicating this error:

    "thumbnail": {
        "error": "SourceImageIOError"
    }
    """
    def __init__(self, filter_spec, *args, **kwargs):
        self.filter_spec = filter_spec
        super(ImageRenditionField, self).__init__(*args, **kwargs)

    def get_attribute(self, instance):
        return instance

    def to_representation(self, image):
        try:
            thumbnail = image.get_rendition(self.filter_spec)

            return OrderedDict([
                ('url', 'http://rca.ac.uk' + thumbnail.url),
                ('width', thumbnail.width),
                ('height', thumbnail.height),
            ])
        except SourceImageIOError:
            return OrderedDict([
                ('error', 'SourceImageIOError'),
            ])


class RCAImageSerializer(ImageSerializer):
    original = ImageRenditionField('original', read_only=True)
    thumbnail = ImageRenditionField('max-165x165', read_only=True)
