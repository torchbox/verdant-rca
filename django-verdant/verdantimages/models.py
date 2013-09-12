from django.core.files import File
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.utils.safestring import mark_safe
from django.utils.html import escape

import StringIO
import PIL.Image
import os.path


class Image(models.Model):
    title = models.CharField(max_length=255)
    file = models.ImageField(upload_to='original_images', width_field='width', height_field='height')
    width = models.IntegerField(editable=False)
    height = models.IntegerField(editable=False)

    def __unicode__(self):
        return self.title

    def get_in_format(self, format):
        if not hasattr(format, 'generate'):
            # assume we've been passed a format spec string, rather than a Format object
            # TODO: keep an in-memory cache of formats, to avoid a db lookup
            format, created = Format.objects.get_or_create(spec=format)

        try:
            rendition = self.renditions.get(format=format)
        except Rendition.DoesNotExist:
            file_field = self.file
            generated_image_file = format.generate(file_field.file)

            rendition = Rendition.objects.create(
                image=self, format=format, file=generated_image_file)

        return rendition

# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(pre_delete, sender=Image)
def image_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)


class Format(models.Model):
    spec = models.CharField(max_length=255, db_index=True)

    def generate(self, input_file):
        """
        Given an input image file as a django.core.files.File object,
        generate an output image in this format, returning it as another
        django.core.files.File object
        """
        input_file.open()
        image = PIL.Image.open(input_file)
        width, height = image.size
        file_format = image.format

        # for now, assume spec is a string in the format '320x200'
        target_width, target_height = [int(i) for i in self.spec.split('x')]

        if width > target_width and height > target_height:
            # downsize image to COVER the target rectangle

            # scale factor if we were to downsize the image to fit the target width
            horz_scale = float(target_width) / width
            # scale factor if we were to downsize the image to fit the target height
            vert_scale = float(target_height) / height

            # choose whichever of these gives a larger image
            scale = max(horz_scale, vert_scale)

            width, height = (int(width * scale), int(height * scale))

            # must ensure image is non-paletted for a high-quality resize
            if image.mode in ['1', 'P']:
                image = image.convert('RGB')

            image = image.resize(
                (width, height),
                PIL.Image.ANTIALIAS
            )

        if width > target_width or height > target_height:
            final_width = min(width, target_width)
            final_height = min(height, target_height)

            # crop image to centre
            left = (width - final_width) / 2
            top = (height - final_height) / 2
            image = image.crop(
                (left, top, left + final_width, top + final_height)
            )

        output = StringIO.StringIO()
        image.save(output, file_format)

        # generate new filename derived from old one, inserting the format string before the extension
        input_filename_parts = os.path.basename(input_file.name).split('.')
        output_filename_parts = input_filename_parts[:-1] + [self.spec] + input_filename_parts[-1:]
        output_filename = '.'.join(output_filename_parts)

        output_file = File(output, name=output_filename)
        input_file.close()

        return output_file


class Rendition(models.Model):
    image = models.ForeignKey('Image', related_name='renditions')
    format = models.ForeignKey('Format', related_name='renditions')
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
