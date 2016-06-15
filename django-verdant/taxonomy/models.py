from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from wagtail.wagtailsnippets.models import register_snippet


@register_snippet
@python_2_unicode_compatible
class Area(models.Model):
    slug = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)

    def __str__(self):
        return self.display_name

    class Meta:
        ordering = ['display_name']


@register_snippet
@python_2_unicode_compatible
class School(models.Model):
    slug = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)

    def __str__(self):
        return self.display_name

    class Meta:
        ordering = ['display_name']


@register_snippet
@python_2_unicode_compatible
class Programme(models.Model):
    school = models.ForeignKey('School', related_name='programmes')
    slug = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    graduation_year = models.PositiveIntegerField(null=True)

    def __str__(self):
        return "{}: {} ({})".format(self.school.display_name, self.display_name, self.graduation_year)

    class Meta:
        unique_together = (
            ('graduation_year', 'slug'),
        )
        ordering = ['-graduation_year', 'display_name']
