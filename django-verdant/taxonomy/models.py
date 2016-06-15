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
    year = models.PositiveIntegerField(
        help_text="This is the year that the academic year finishes. For "
                  "example, this should be set to '2017' for the '2016/17' "
                  "academic year")
    slug = models.CharField(
        max_length=255,
        help_text="This field is used to link this school with previous years. "
                  "The display name may be changed year-on-year but the slug "
                  "must remain the same. It must contain lowercase letters only."
    )
    display_name = models.CharField(max_length=255)

    def __str__(self):
        return "{} ({})".format(self.display_name, self.year)

    class Meta:
        unique_together = (
            ('year', 'slug'),
        )
        ordering = ['-year', 'display_name']


@register_snippet
@python_2_unicode_compatible
class Programme(models.Model):
    school = models.ForeignKey('School', related_name='programmes')
    slug = models.CharField(
        max_length=255,
        help_text="Like the slug field above, this field must not change "
                  "year-on-year and it must only contain lowercase letters."
    )
    display_name = models.CharField(max_length=255)

    def __str__(self):
        return "{} ({})".format(self.display_name, self.school.year)

    class Meta:
        unique_together = (
            ('school', 'slug'),
        )
        ordering = ['display_name']
