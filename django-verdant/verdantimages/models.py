from django.core.files import File
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.utils.safestring import mark_safe
from django.utils.html import escape

import StringIO
import PIL.Image
import os.path

from taggit.managers import TaggableManager

from verdantimages import image_ops


class Image(models.Model):
    title = models.CharField(max_length=255)
    file = models.ImageField(upload_to='original_images', width_field='width', height_field='height')
    width = models.IntegerField(editable=False)
    height = models.IntegerField(editable=False)

    tags = TaggableManager(help_text=None)

    def __unicode__(self):
        return self.title

    def get_rendition(self, filter):
        if not hasattr(filter, 'process_image'):
            # assume we've been passed a filter spec string, rather than a Filter object
            # TODO: keep an in-memory cache of filters, to avoid a db lookup
            filter, created = Filter.objects.get_or_create(spec=filter)

        try:
            rendition = self.renditions.get(filter=filter)
        except Rendition.DoesNotExist:
            file_field = self.file
            generated_image_file = filter.process_image(file_field.file)

            rendition = Rendition.objects.create(
                image=self, filter=filter, file=generated_image_file)

        return rendition

# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(pre_delete, sender=Image)
def image_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)


class Filter(models.Model):
    """
    Represents an operation that can be applied to an Image to produce a rendition
    appropriate for final display on the website. Usually this would be a resize operation,
    but could potentially involve colour processing, etc.
    """
    spec = models.CharField(max_length=255, db_index=True)

    OPERATION_NAMES = {
        'max': image_ops.resize_to_max,
        'min': image_ops.resize_to_min,
        'width': image_ops.resize_to_width,
        'height': image_ops.resize_to_height,
        'fill': image_ops.resize_to_fill,
    }

    def __init__(self, *args, **kwargs):
        super(Filter, self).__init__(*args, **kwargs)
        self.method = None  # will be populated when needed, by parsing the spec string

    def _parse_spec_string(self):
        # parse the spec string, which is formatted as (method)-(arg),
        # and save the results to self.method and self.method_arg
        try:
            (method_name, method_arg_string) = self.spec.split('-')
            self.method = Filter.OPERATION_NAMES[method_name]

            if method_name in ('max', 'min', 'fill'):
                # method_arg_string is in the form 640x480
                (width, height) = [int(i) for i in method_arg_string.split('x')]
                self.method_arg = (width, height)
            else:
                # method_arg_string is a single number
                self.method_arg = int(method_arg_string)

        except (ValueError, KeyError):
            raise ValueError("Invalid image filter spec: %r" % self.spec)

    def process_image(self, input_file):
        """
        Given an input image file as a django.core.files.File object,
        generate an output image with this filter applied, returning it
        as another django.core.files.File object
        """
        if not self.method:
            self._parse_spec_string()

        input_file.open()
        image = PIL.Image.open(input_file)
        file_format = image.format

        # perform the resize operation
        image = self.method(image, self.method_arg)

        output = StringIO.StringIO()
        image.save(output, file_format)

        # generate new filename derived from old one, inserting the filter spec string before the extension
        input_filename_parts = os.path.basename(input_file.name).split('.')
        output_filename_parts = input_filename_parts[:-1] + [self.spec] + input_filename_parts[-1:]
        output_filename = '.'.join(output_filename_parts)

        output_file = File(output, name=output_filename)
        input_file.close()

        return output_file


class Rendition(models.Model):
    image = models.ForeignKey('Image', related_name='renditions')
    filter = models.ForeignKey('Filter', related_name='renditions')
    file = models.ImageField(upload_to='images', width_field='width', height_field='height')
    width = models.IntegerField(editable=False)
    height = models.IntegerField(editable=False)

    @property
    def url(self):
        return self.file.url

    def img_tag(self):
        return mark_safe(
            '<img src="%s" width="%d" height="%d" alt="%s">' % (escape(self.url), self.width, self.height, escape(self.image.title))
        )

# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(pre_delete, sender=Rendition)
def rendition_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)
