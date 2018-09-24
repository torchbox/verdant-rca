from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import slugify

from modelcluster.models import ClusterableModel
from modelcluster.fields import ParentalKey

from wagtail.wagtailadmin.edit_handlers import FieldPanel, InlinePanel


@python_2_unicode_compatible
class Area(models.Model):
    """
    Used for non-academic areas (Administration, AlumniRCA, etc)
    """
    slug = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)

    api_fields = ['slug']

    def __str__(self):
        return self.display_name

    class Meta:
        ordering = ['display_name']


@python_2_unicode_compatible
class School(ClusterableModel):
    """
    Used for schools (School of Comminication, School of Architecture, etc)
    """
    slug = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)

    api_fields = ['slug']

    panels = [
        FieldPanel('slug'),
        FieldPanel('display_name'),
        InlinePanel('historical_display_names', label="Historical display names"),
    ]

    def get_display_name_for_year(self, year):
        if not year:
            return self.display_name

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
        help_text="This is the last year that the name was used. For example, if "
                  "the name was changed at the beginning of the 2016/17 academic "
                  "year, this field should be set to 2016."
    )
    display_name = models.CharField(max_length=255)

    class Meta:
        ordering = ['end_year']


@python_2_unicode_compatible
class Programme(ClusterableModel):
    """
    Used for programmes (Animation, Interior design, etc).
    """
    school = models.ForeignKey('School', related_name='programmes')
    slug = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    disabled = models.BooleanField(default=False)

    api_fields = ['slug', 'school']

    panels = [
        FieldPanel('school'),
        FieldPanel('slug'),
        FieldPanel('display_name'),
        InlinePanel('historical_display_names', label="Historical display names"),
        FieldPanel('disabled'),
    ]

    def get_display_name_for_year(self, year):
        if not year:
            return self.display_name

        hdn = self.historical_display_names.filter(end_year__gte=year).order_by('end_year').first()
        if hdn:
            return hdn.display_name
        else:
            return self.display_name

    def __str__(self):
        return self.display_name

    class Meta:
        ordering = ['display_name']


class ProgrammeHistoricalDisplayName(models.Model):
    """
    Used to store names that were used for a particular programme in the past.

    Like schools, programmes can also change their name over time. If this
    happens, the old name must be inserted here noting the last year the name
    was used. This allows us to look up the correct name to use for a school
    when displaying old content.
    """
    school = ParentalKey('Programme', related_name='historical_display_names')
    end_year = models.PositiveIntegerField(
        help_text="This is the last year that the name was used. For example, if "
                  "the name was changed at the beginning of the 2016/17 academic "
                  "year, this field should be set to 2016."
    )
    display_name = models.CharField(max_length=255)

    class Meta:
        ordering = ['end_year']


@python_2_unicode_compatible
class DegreeLevel(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.CharField(max_length=255, unique=True, blank=True)

    def __str__(self):
        return self.name

    def clean(self):
        super(DegreeLevel, self).clean()
        self.slug = self.find_available_slug(self.name)

    def find_available_slug(self, title):
        requested_slug = slugify(title)
        slug = requested_slug
        number = 1
        while self.__class__.objects.filter(slug=slug).exists():
            slug = requested_slug + '-' + str(number)
            number += 1
        return slug

    panels = [
        FieldPanel('name'),
    ]
