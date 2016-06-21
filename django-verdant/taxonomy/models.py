from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from modelcluster.models import ClusterableModel
from modelcluster.fields import ParentalKey

from wagtail.wagtailadmin.edit_handlers import FieldPanel, InlinePanel
from wagtail.wagtailsnippets.models import register_snippet


@register_snippet
@python_2_unicode_compatible
class Area(models.Model):
    """
    Used for non-academic areas (Administration, AlumniRCA, etc)
    """
    slug = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)

    def __str__(self):
        return self.display_name

    class Meta:
        ordering = ['display_name']


@register_snippet
@python_2_unicode_compatible
class School(ClusterableModel):
    """
    Used for schools (School of Comminication, School of Architecture, etc)
    """
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
    """
    Used to store names that were used for a particular school in the past.

    Schools can change their name over time. If this happens, the old name must
    be inserted here noting the last year the name was used. This allows us to
    look up the correct name to use for a school when displaying old content.
    """
    school = ParentalKey('School', related_name='historical_display_names')
    end_year = models.PositiveIntegerField(
        help_text="This is the last year that the name was used. For example, if"
                  "the name was changed at the beginning of the 2016/17 academic"
                  "year, this field should be set to 2016."
    )
    display_name = models.CharField(max_length=255)

    class Meta:
        ordering = ['end_year']


@register_snippet
@python_2_unicode_compatible
class Programme(models.Model):
    """
    Used for programmes (Animation, Interior design, etc).

    Unlike areas and schools, programmes are linked to a single year. This is to
    allow the programmes to be easily changed year on year.
    """
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
