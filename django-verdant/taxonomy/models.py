from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from modelcluster.models import ClusterableModel
from modelcluster.fields import ParentalKey

from wagtail.wagtailadmin.edit_handlers import FieldPanel, InlinePanel
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
class School(ClusterableModel):
    slug = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)

    panels = [
        FieldPanel('slug'),
        FieldPanel('display_name'),
        InlinePanel('historical_display_names', label="Historical display names"),
    ]

    def get_display_name_for_year(self, year):
        hdn = self.historical_display_names.filter(end_year__gte=year).order_by('end_year').first()
        if hdn:
            return hdn.display_name
        else:
            return self.display_name


    def __str__(self):
        return self.display_name

    class Meta:
        ordering = ['display_name']


class SchoolHistoricalDisplayName(models.Model):
    school = ParentalKey('School', related_name='historical_display_names')
    end_year = models.PositiveIntegerField()
    display_name = models.CharField(max_length=255)

    class Meta:
        ordering = ['end_year']


@register_snippet
@python_2_unicode_compatible
class Programme(models.Model):
    school = models.ForeignKey('School', related_name='programmes')
    slug = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    graduation_year = models.PositiveIntegerField()

    def __str__(self):
        return "{}: {} ({})".format(self.school.get_display_name_for_year(self.graduation_year), self.display_name, self.graduation_year)

    class Meta:
        unique_together = (
            ('graduation_year', 'slug'),
        )
        ordering = ['-graduation_year', 'display_name']
