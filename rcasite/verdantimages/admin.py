from django.contrib import admin
from django.conf import settings

from verdantimages.models import Image

if hasattr(settings, 'VERDANTIMAGES_IMAGE_MODEL') and settings.VERDANTIMAGES_IMAGE_MODEL != 'verdantimages.Image':
    # This installation provides its own custom image class;
    # to avoid confusion, we won't expose the unused verdantimages.Image class
    # in the admin.
    pass
else:
    admin.site.register(Image)
