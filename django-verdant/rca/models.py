from datetime import date
import datetime
import logging

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.contrib import messages
from django.db import models
from django.db.models import Min
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from core.models import Page, Orderable
from core.fields import RichTextField
from cluster.fields import ParentalKey

from verdantadmin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel, PageChooserPanel
from verdantimages.edit_handlers import ImageChooserPanel
from verdantimages.models import AbstractImage, AbstractRendition
from verdantdocs.edit_handlers import DocumentChooserPanel
from verdantsnippets.edit_handlers import SnippetChooserPanel
from verdantsnippets.models import register_snippet

from cluster.tags import ClusterTaggableManager
from taggit.models import TaggedItemBase

from donations.forms import DonationForm
from donations.mail_admins import mail_exception, full_exc_info
import stripe

# RCA defines its own custom image class to replace verdantimages.Image,
# providing various additional data fields
class RcaImage(AbstractImage):
    alt = models.CharField(max_length=255, blank=True)
    creator = models.CharField(max_length=255, blank=True)
    year = models.CharField(max_length=255, blank=True)
    medium = models.CharField(max_length=255, blank=True)
    dimensions = models.CharField(max_length=255, blank=True)
    permission = models.CharField(max_length=255, blank=True)
    photographer = models.CharField(max_length=255, blank=True)
    rca_content_id = models.CharField(max_length=255, blank=True, editable=False) # for import
    eprint_docid = models.CharField(max_length=255, blank=True, editable=False) # for import

    indexed_fields = ('creator', 'photographer')

    @property
    def default_alt_text(self):
        return self.alt

    def caption_lines(self):
        if self.creator:
            first_line = u"%s, %s" % (self.title, self.creator)
        else:
            first_line = self.title

        lines = [first_line]

        if self.medium:
            lines.append(self.medium)

        bottom_line_items = []
        if self.dimensions:
            bottom_line_items.append(self.dimensions)
        if self.permission:
            bottom_line_items.append(u"\u00a9 %s" % self.permission)  # u00a9 = copyright symbol
        if self.photographer:
            bottom_line_items.append("Photographer: %s" % self.photographer)

        if bottom_line_items:
            lines.append(' | '.join(bottom_line_items))

        return lines

    def caption_html(self):
        # use caption_lines, but replace top line with a version that italicises the title
        lines = self.caption_lines()

        if self.creator:
            lines[0] = mark_safe(u"<i>%s</i>, %s" % (conditional_escape(self.title), conditional_escape(self.creator)))
        else:
            lines[0] = mark_safe(u"<i>%s</i>" % conditional_escape(self.title))

        escaped_lines = [conditional_escape(line) for line in lines]
        return mark_safe('<br />'.join(escaped_lines))


# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(pre_delete, sender=RcaImage)
def image_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)

class RcaRendition(AbstractRendition):
    image = models.ForeignKey('RcaImage', related_name='renditions')

    class Meta:
        unique_together = (
            ('image', 'filter'),
        )

# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(pre_delete, sender=RcaRendition)
def rendition_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)


AREA_CHOICES = (
    ('helenhamlyn', 'The Helen Hamlyn Centre for Design'),
    ('innovationrca', 'InnovationRCA'),
    ('research', 'Research'),
    ('knowledgeexchange', 'Knowledge Exchange'),
    ('showrca', 'Show RCA'),
    ('fuelrca', 'Fuel RCA'),
    ('sustainrca', 'SustainRCA'),
    ('support', 'Support'),
)

EVENT_AUDIENCE_CHOICES = (
    ('public', 'Public'),
    ('rcaonly', 'RCA only'),
    ('openday', 'Open Day'),
    ('rcatalks', 'RCA talks'),
)

EVENT_LOCATION_CHOICES = (
    ('kensington', 'Kensington'),
    ('battersea', 'Battersea'),
    ('other', 'Other (enter below)')
)

CAMPUS_CHOICES = (
    ('kensington', 'Kensington'),
    ('battersea', 'Battersea'),
)

EVENT_GALLERY_CHOICES = (
    ('gallery1', 'Gallery 1'),
    ('gallery2', 'Gallery 2'),
    ('galleryn', 'Gallery N'),
)

WORK_TYPES_CHOICES = (
    ('journalarticle', 'Journal Article'),
    ('thesis', 'Thesis'),
    ('booksection', 'Book Section'),
    ('monograph', 'Monograph'),
    ('printepublication', 'Printed Publication'),
    ('conferenceorworkshop', 'Conference or Workshop'),
    ('artordesignobject', 'Art or design object'),
    ('showexhibitionorevent', 'Show, Exhibition or Event'),
    ('teachingresource', 'Teaching Resource'),
    ('residency', 'Residency'),
    ('other', 'Other (enter below)'),
)

WORK_THEME_CHOICES = (
    ('culturesofcurating', 'Cultures of Curating'),
    ('designinnovationandsociety', 'Design, Innovation and Society'),
    ('dialoguesofformandsurface', 'Dialogues of Form and Surface'),
    ('imageandlanguage', 'Image and Language')
)


SCHOOL_CHOICES = (
    ('schoolofarchitecture', 'School of Architecture'),
    ('schoolofcommunication', 'School of Communication'),
    ('schoolofdesign', 'School of Design'),
    ('schooloffineart', 'School of Fine Art'),
    ('schoolofhumanities', 'School of Humanities'),
    ('schoolofmaterial', 'School of Material'),
    ('schoolofappliedart', 'School of Applied Art'),
    ('schoolofarchitecturedesign', 'School of Architecture & Design'),
    ('schoolofcommunications', 'School of Communcations'),
    ('schooloffashiontextiles', 'School of Fashion & Textiles'),
    ('schoolofdesignforproduction', 'School of Design for Production'),
    ('helenhamlyn', 'The Helen Hamlyn Centre for Design'),
    ('rectorate', 'Rectorate'),
)

HISTORICAL_PROGRAMMES = {
    '2007': (
        ('ceramicsglass', 'Ceramics & Glass'),
        ('goldsmithingsilversmithingmetalworkjewellery', 'Goldsmithing, Silversmithing, Metalwork & Jewellery'),
        ('architecture', 'Architecture'),
        ('designinteractions', 'Design Interactions'),
        ('designproducts', 'Design Products'),
        ('industrialdesignengineering', 'Industrial Design Engineering'),
        ('vehicledesign', 'Vehicle Design'),
        ('animation', 'Animation'),
        ('communicationartdesign', 'Communication Art & Design'),
        ('fashionmenswear', 'Fashion Menswear'),
        ('fashionwomenswear', 'Fashion Womenswear'),
        ('textiles', 'Textiles'),
        ('painting', 'Painting'),
        ('photography', 'Photography'),
        ('printmaking', 'Printmaking'),
        ('sculpture', 'Sculpture'),
        ('conservation', 'Conservation'),
        ('criticalhistoricalstudies', 'Critical & Historical Studies'),
        ('curatingcontemporaryart', 'Curating Contemporary Art'),
        ('historyofdesign', 'History of Design'),
    ),
    '2008': (
        ('ceramicsglass', 'Ceramics & Glass'),
        ('goldsmithingsilversmithingmetalworkjewellery', 'Goldsmithing, Silversmithing, Metalwork & Jewellery'),
        ('architecture', 'Architecture'),
        ('designinteractions', 'Design Interactions'),
        ('designproducts', 'Design Products'),
        ('animation', 'Animation'),
        ('communicationartdesign', 'Communication Art & Design'),
        ('fashionmenswear', 'Fashion Menswear'),
        ('fashionwomenswear', 'Fashion Womenswear'),
        ('textiles', 'Textiles'),
        ('innovationdesignengineering', 'Innovation Design Engineering'),
        ('vehicledesign', 'Vehicle Design'),
        ('painting', 'Painting'),
        ('photography', 'Photography'),
        ('printmaking', 'Printmaking'),
        ('sculpture', 'Sculpture'),
        ('conservation', 'Conservation'),
        ('criticalhistoricalstudies', 'Critical & Historical Studies'),
        ('curatingcontemporaryart', 'Curating Contemporary Art'),
        ('historyofdesign', 'History of Design'),
    ),
    '2009': (
        ('ceramicsglass', 'Ceramics & Glass'),
        ('goldsmithingsilversmithingmetalworkjewellery', 'Goldsmithing, Silversmithing, Metalwork & Jewellery'),
        ('architecture', 'Architecture'),
        ('designinteractions', 'Design Interactions'),
        ('designproducts', 'Design Products'),
        ('animation', 'Animation'),
        ('communicationartdesign', 'Communication Art & Design'),
        ('fashionmenswear', 'Fashion Menswear'),
        ('fashionwomenswear', 'Fashion Womenswear'),
        ('textiles', 'Textiles'),
        ('innovationdesignengineering', 'Innovation Design Engineering'),
        ('vehicledesign', 'Vehicle Design'),
        ('painting', 'Painting'),
        ('photography', 'Photography'),
        ('printmaking', 'Printmaking'),
        ('sculpture', 'Sculpture'),
        ('conservation', 'Conservation'),
        ('criticalhistoricalstudies', 'Critical & Historical Studies'),
        ('curatingcontemporaryart', 'Curating Contemporary Art'),
        ('historyofdesign', 'History of Design'),
    ),
    '2010': (
        ('architecture', 'Architecture'),
        ('animation', 'Animation'),
        ('visualcommunication', 'Visual Communication'),
        ('designinteractions', 'Design Interactions'),
        ('designproducts', 'Design Products'),
        ('innovationdesignengineering', 'Innovation Design Engineering'),
        ('vehicledesign', 'Vehicle Design'),
        ('painting', 'Painting'),
        ('photography', 'Photography'),
        ('printmaking', 'Printmaking'),
        ('sculpture', 'Sculpture'),
        ('criticalhistoricalstudies', 'Critical & Historical Studies'),
        ('criticalwritinginartdesign', 'Critical Writing in Art & Design'),
        ('curatingcontemporaryart', 'Curating Contemporary Art'),
        ('historyofdesign', 'History of Design'),
        ('ceramicsglass', 'Ceramics & Glass'),
        ('fashionmenswear', 'Fashion Menswear'),
        ('fashionwomenswear', 'Fashion Womenswear'),
        ('goldsmithingsilversmithingmetalworkjewellery', 'Goldsmithing, Silversmithing, Metalwork & Jewellery'),
        ('textiles', 'Textiles'),
    ),
    '2011': (
        ('architecture', 'Architecture'),
        ('animation', 'Animation'),
        ('visualcommunication', 'Visual Communication'),
        ('designinteractions', 'Design Interactions'),
        ('designproducts', 'Design Products'),
        ('innovationdesignengineering', 'Innovation Design Engineering'),
        ('vehicledesign', 'Vehicle Design'),
        ('painting', 'Painting'),
        ('photography', 'Photography'),
        ('printmaking', 'Printmaking'),
        ('sculpture', 'Sculpture'),
        ('criticalhistoricalstudies', 'Critical & Historical Studies'),
        ('criticalwritinginartdesign', 'Critical Writing in Art & Design'),
        ('curatingcontemporaryart', 'Curating Contemporary Art'),
        ('historyofdesign', 'History of Design'),
        ('ceramicsglass', 'Ceramics & Glass'),
        ('fashionmenswear', 'Fashion Menswear'),
        ('fashionwomenswear', 'Fashion Womenswear'),
        ('goldsmithingsilversmithingmetalworkjewellery', 'Goldsmithing, Silversmithing, Metalwork & Jewellery'),
        ('textiles', 'Textiles'),
    ),
    '2012': (
        ('architecture', 'Architecture'),
        ('animation', 'Animation'),
        ('visualcommunication', 'Visual Communication'),
        ('designinteractions', 'Design Interactions'),
        ('designproducts', 'Design Products'),
        ('innovationdesignengineering', 'Innovation Design Engineering'),
        ('vehicledesign', 'Vehicle Design'),
        ('painting', 'Painting'),
        ('photography', 'Photography'),
        ('printmaking', 'Printmaking'),
        ('sculpture', 'Sculpture'),
        ('criticalhistoricalstudies', 'Critical & Historical Studies'),
        ('criticalwritinginartdesign', 'Critical Writing in Art & Design'),
        ('curatingcontemporaryart', 'Curating Contemporary Art'),
        ('historyofdesign', 'History of Design'),
        ('ceramicsglass', 'Ceramics & Glass'),
        ('fashionmenswear', 'Fashion Menswear'),
        ('fashionwomenswear', 'Fashion Womenswear'),
        ('goldsmithingsilversmithingmetalworkjewellery', 'Goldsmithing, Silversmithing, Metalwork & Jewellery'),
        ('textiles', 'Textiles'),
    ),
    '2013': (
        ('architecture', 'Architecture'),
        ('interiordesign', 'Interior Design'),
        ('animation', 'Animation'),
        ('informationexperiencedesign', 'Information Experience Design'),
        ('visualcommunication', 'Visual Communication'),
        ('designinteractions', 'Design Interactions'),
        ('designproducts', 'Design Products'),
        ('globalinnovationdesign', 'Global Innovation Design'),
        ('innovationdesignengineering', 'Innovation Design Engineering'),
        ('servicedesign', 'Service Design'),
        ('vehicledesign', 'Vehicle Design'),
        ('painting', 'Painting'),
        ('photography', 'Photography'),
        ('printmaking', 'Printmaking'),
        ('sculpture', 'Sculpture'),
        ('criticalhistoricalstudies', 'Critical & Historical Studies'),
        ('criticalwritinginartdesign', 'Critical Writing in Art & Design'),
        ('curatingcontemporaryart', 'Curating Contemporary Art'),
        ('historyofdesign', 'History of Design'),
        ('ceramicsglass', 'Ceramics & Glass'),
        ('goldsmithingsilversmithingmetalworkjewellery', 'Goldsmithing, Silversmithing, Metalwork & Jewellery'),
        ('fashionmenswear', 'Fashion Menswear'),
        ('fashionwomenswear', 'Fashion Womenswear'),
        ('textiles', 'Textiles'),
        ('drawingstudio', 'Drawing Studio'),
    ),
}

ALL_PROGRAMMES = list(set([x for year_tuple in HISTORICAL_PROGRAMMES.values() for x in year_tuple]))

# PROGRAMME_CHOICES is the last/current year from HISTORICAL_PROGRAMMES
PROGRAMME_CHOICES = HISTORICAL_PROGRAMMES[sorted(HISTORICAL_PROGRAMMES.keys())[-1]]

SCHOOL_PROGRAMME_MAP = {
    '2014': {
        'schoolofarchitecture': ['architecture', 'interiordesign'],
        'schoolofcommunication': ['animation', 'informationexperiencedesign', 'visualcommunication'],
        'schoolofdesign': ['designinteractions', 'designproducts', 'globalinnovationdesign', 'innovationdesignengineering', 'servicedesign', 'vehicledesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['criticalhistoricalstudies', 'criticalwritinginartdesign', 'curatingcontemporaryart', 'historyofdesign'],
        'schoolofmaterial': ['ceramicsglass', 'goldsmithingsilversmithingmetalworkjewellery', 'fashionmenswear', 'fashionwomenswear', 'textiles'],
        'helenhamlyn': [],
        'rectorate': [],
    },
    '2013': {
        'schoolofarchitecture': ['architecture', 'interiordesign'],
        'schoolofcommunication': ['animation', 'informationexperiencedesign', 'visualcommunication'],
        'schoolofdesign': ['designinteractions', 'designproducts', 'innovationdesignengineering', 'servicedesign', 'vehicledesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['criticalhistoricalstudies', 'criticalwritinginartdesign', 'curatingcontemporaryart', 'historyofdesign'],
        'schoolofmaterial': ['ceramicsglass', 'goldsmithingsilversmithingmetalworkjewellery', 'fashionmenswear', 'fashionwomenswear', 'textiles'],
        'helenhamlyn': [],
        'rectorate': [],
        },
    '2012': {
        'schoolofarchitecture': ['architecture', 'animation'],
        'schoolofcommunication': ['animation', 'visualcommunication'],
        'schoolofdesign': ['designinteractions', 'designproducts', 'innovationdesignengineering', 'vehicledesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['criticalhistoricalstudies', 'criticalwritinginartdesign', 'curatingcontemporaryart', 'historyofdesign'],
        'schoolofmaterial': ['ceramicsglass', 'goldsmithingsilversmithingmetalworkjewellery', 'fashionmenswear', 'fashionwomenswear', 'textiles'],
    },
    '2011': {
        'schoolofarchitecture': ['architecture', 'animation'],
        'schoolofcommunication': ['animation', 'visualcommunication'],
        'schoolofdesign': ['designinteractions', 'designproducts', 'innovationdesignengineering', 'vehicledesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['criticalhistoricalstudies', 'criticalwritinginartdesign', 'curatingcontemporaryart', 'historyofdesign'],
        'schoolofmaterial': ['ceramicsglass', 'goldsmithingsilversmithingmetalworkjewellery', 'fashionmenswear', 'fashionwomenswear', 'textiles'],
    },
    '2010': {
        'schoolofarchitecture': ['architecture', 'animation'],
        'schoolofcommunication': ['animation', 'visualcommunication'],
        'schoolofdesign': ['designinteractions', 'designproducts', 'innovationdesignengineering', 'vehicledesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['criticalhistoricalstudies', 'criticalwritinginartdesign', 'curatingcontemporaryart', 'historyofdesign'],
        'schoolofmaterial': ['ceramicsglass', 'goldsmithingsilversmithingmetalworkjewellery', 'fashionmenswear', 'fashionwomenswear', 'textiles'],
    },
    '2009': {
        'schoolofappliedart': ['ceramicsglass', 'goldsmithingsilversmithingmetalworkjewellery'],
        'schoolofarchitecturedesign': ['architecture', 'designinteractions', 'designproducts'],
        'schoolofcommunications': ['animation', 'communicationartdesign'],
        'schooloffashiontextiles': ['fashionmenswear', 'fashionwomenswear', 'textiles'],
        'schoolofdesignforproduction': ['innovationdesignengineering', 'vehicledesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['conservation', 'criticalhistoricalstudies', 'curatingcontemporaryart', 'historyofdesign'],
    },
    '2008': {
        'schoolofappliedart': ['ceramicsglass', 'goldsmithingsilversmithingmetalworkjewellery'],
        'schoolofarchitecturedesign': ['architecture', 'designinteractions', 'designproducts'],
        'schoolofcommunications': ['animation', 'communicationartdesign'],
        'schooloffashiontextiles': ['fashionmenswear', 'fashionwomenswear', 'textiles'],
        'schoolofdesignforproduction': ['innovationdesignengineering', 'vehicledesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['conservation', 'criticalhistoricalstudies', 'curatingcontemporaryart', 'historyofdesign'],
    },
    '2007': {
        'schoolofappliedart': ['ceramicsglass', 'goldsmithingsilversmithingmetalworkjewellery'],
        'schoolofarchitecturedesign': ['architecture', 'designinteractions', 'designproducts', 'industrialdesignengineering', 'vehicledesign'],
        'schoolofcommunications': ['animation', 'communicationartdesign'],
        'schooloffashiontextiles': ['fashionmenswear', 'fashionwomenswear', 'textiles'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['conservation', 'criticalhistoricalstudies', 'curatingcontemporaryart', 'historyofdesign'],
    },
}

# Make sure the values in SCHOOL_PROGRAMME_MAP are valid (`sum(list, [])` flattens a list)
# 1. check schools
assert set(sum([mapping.keys() for mapping in SCHOOL_PROGRAMME_MAP.values()], []))\
        .issubset(set(dict(SCHOOL_CHOICES)))
# 2. check programmes
assert set(sum([sum(mapping.values(), []) for mapping in SCHOOL_PROGRAMME_MAP.values()], []))\
        .issubset(set(dict(ALL_PROGRAMMES)))

# TODO: remove this line, needed temporarily until the year filters are done
SCHOOL_PROGRAMME_MAP = SCHOOL_PROGRAMME_MAP[sorted(SCHOOL_PROGRAMME_MAP.keys())[-1]]

SUBJECT_CHOICES = (
    ('animation', 'Animation'),
    ('architecture', 'Architecture'),
    ('ceramicsglass', 'Ceramics & Glass'),
    ('curatingcontemporaryartcollegebased', 'Curating Contemporary Art (College-based)'),
    ('curatingcontemporaryartworkbased', 'Curating Contemporary Art (Work-based)'),
    ('criticalhistoricalstudies', 'Critical & Historical Studies'),
    ('criticalwritinginartdesign', 'Critical Writing In Art & Design'),
    ('designinteractions', 'Design Interactions'),
    ('designproducts', 'Design Products'),
    ('drawingstudio', 'Drawing Studio'),
    ('fashionmenswear', 'Fashion Menswear'),
    ('fashionwomenswear', 'Fashion Womenswear'),
    ('innovationdesignengineering', 'Innovation Design Engineering'),
    ('historyofdesign', 'History of Design'),
    ('painting', 'Painting'),
    ('photography', 'Photography'),
    ('printmaking', 'Printmaking'),
    ('sculpture', 'Sculpture'),
    ('goldsmithingsilversmithingmetalworkjewellery', 'Goldsmithing, Silversmithing, Metalwork & Jewellery'),
    ('textiles', 'Textiles'),
    ('vehicledesign', 'Vehicle Design'),
    ('visualcommunication', 'Visual Communication'),
)

QUALIFICATION_CHOICES = (
    ('ma', 'MA'),
    ('mphil', 'MPhil'),
    ('phd', 'PhD'),
    ('researchstudent', 'Research Student'),
)

RESEARCH_TYPES_CHOICES = (
    ('student', 'Student'),
    ('staff', 'Staff'),
)

STAFF_TYPES_CHOICES = (
    ('academic', 'Academic'),
    ('technical', 'Technical'),
    ('administrative', 'Administrative'),
)

TWITTER_FEED_HELP_TEXT = "Replace the default Twitter feed by providing an alternative Twitter handle (without the @ symbol)"

# Generic social fields abstract class to add social image/text to any new content type easily.
class SocialFields(models.Model):
    social_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    social_text = models.CharField(max_length=255, blank=True)

    class Meta:
        abstract = True

# Carousel item abstract class - all carousels basically require the same fields
class CarouselItemFields(models.Model):
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    overlay_text = models.CharField(max_length=255, blank=True)
    link = models.URLField(blank=True)
    embedly_url = models.URLField('Vimeo URL', blank=True)
    poster_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('overlay_text'),
        FieldPanel('link'),
        FieldPanel('embedly_url'),
        ImageChooserPanel('poster_image'),
    ]

    class Meta:
        abstract = True


# == Snippet: Advert ==

class Advert(models.Model):
    page = models.ForeignKey('core.Page', related_name='adverts', null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255, help_text="bold text")
    plain_text = models.CharField(max_length=255, blank=True)
    show_globally = models.BooleanField(default=False)

    panels = [
        PageChooserPanel('page'),
        FieldPanel('url'),
        FieldPanel('text'),
        FieldPanel('plain_text'),
        FieldPanel('show_globally'),
    ]

    def __unicode__(self):
        return self.text

register_snippet(Advert)

class AdvertPlacement(models.Model):
    page = ParentalKey('core.Page', related_name='advert_placements')
    advert = models.ForeignKey('rca.Advert', related_name='+')

# == Snippet: Custom Content Module ==

class CustomContentModuleBlock(Orderable):
    content_module = ParentalKey('rca.CustomContentModule', related_name='blocks')
    link = models.ForeignKey('core.Page', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    item_title = models.CharField(max_length=255)
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text="The image for the module block")
    text = models.CharField(max_length=255, blank=True)

    panels = [
        PageChooserPanel('link'),
        FieldPanel('item_title'),
        ImageChooserPanel('image'),
        FieldPanel('text')
    ]

class CustomContentModule(models.Model):
    title = models.CharField(max_length=255)

    def __unicode__(self):
        return self.title

CustomContentModule.panels = [
    FieldPanel('title'),
    InlinePanel(CustomContentModule, 'blocks', label=""),
]

register_snippet(CustomContentModule)

class CustomeContentModulePlacement(models.Model):
    page = ParentalKey('core.Page', related_name='custom_content_module_placements')
    custom_content_module = models.ForeignKey('rca.CustomContentModule', related_name='+')

# == Snippet: Reusable rich text field ==
class ReusableTextSnippet(models.Model):
    name = models.CharField(max_length=255)
    text = RichTextField()
    panels = [
        FieldPanel('name'),
        FieldPanel('text', classname="full")
    ]

    def __unicode__(self):
        return self.name

register_snippet(ReusableTextSnippet)

class ReusableTextSnippetPlacement(models.Model):
    page = ParentalKey('core.Page', related_name='reusable_text_snippet_placements')
    reusable_text_snippet = models.ForeignKey('rca.ReusableTextSnippet', related_name='+')

# == Snippet: Contacts ==

class ContactSnippetPhone(Orderable):
    page = ParentalKey('rca.ContactSnippet', related_name='contact_phone')
    phone_number = models.CharField(max_length=255)

    panels = [
        FieldPanel('phone_number')
    ]

class ContactSnippetEmail(Orderable):
    page = ParentalKey('rca.ContactSnippet', related_name='contact_email')
    email_address = models.CharField(max_length=255)

    panels = [
        FieldPanel('email_address')
    ]

class ContactSnippet(models.Model):
    title = models.CharField(max_length=255, help_text='This is the reference name for the contact. This is not displayed on the frontend.')
    contact_title = models.CharField(max_length=255, blank=True, help_text="This is the optional title, displayed on the frontend")
    contact_address = models.TextField(blank=True)
    contact_link = models.URLField(blank=True)
    contact_link_text = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return self.title

ContactSnippet.panels = [
    FieldPanel('title'),
    FieldPanel('contact_title'),
    FieldPanel('contact_address'),
    FieldPanel('contact_link'),
    FieldPanel('contact_link_text'),
    InlinePanel(ContactSnippet, 'contact_email', label="Contact phone numbers/emails"),
    InlinePanel(ContactSnippet, 'contact_phone', label="Contact phone number"),
]


register_snippet(ContactSnippet)

class ContactSnippetPlacement(models.Model):
    page = ParentalKey('core.Page', related_name='contact_snippet_placements')
    contact_snippet = models.ForeignKey('rca.ContactSnippet', related_name='+')

# == School page ==

class SchoolPageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.SchoolPage', related_name='carousel_items')

class SchoolPageContactTelEmail(Orderable):
    page = ParentalKey('rca.SchoolPage', related_name='contact_tel_email')
    phone_number = models.CharField(max_length=255, blank=True)
    email = models.CharField(max_length=255, blank=True)

    panels = [
        FieldPanel('phone_number'),
        FieldPanel('email'),
    ]

class SchoolPageContactPhone(Orderable):
    page = ParentalKey('rca.SchoolPage', related_name='contact_phone')
    phone_number = models.CharField(max_length=255)

    panels = [
        FieldPanel('phone_number')
    ]

class SchoolPageContactEmail(Orderable):
    page = ParentalKey('rca.SchoolPage', related_name='contact_email')
    email_address = models.CharField(max_length=255)

    panels = [
        FieldPanel('email_address')
    ]

class SchoolPageRelatedLink(Orderable):
    page = ParentalKey('rca.SchoolPage', related_name='related_links')
    link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    link_text = models.CharField(max_length=255, help_text="Alternative link title (default is target page's title)")

    panels = [
        PageChooserPanel('link'),
        FieldPanel('link_text'),
    ]

class SchoolPageAd(Orderable):
    page = ParentalKey('rca.SchoolPage', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+')

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]


class SchoolPage(Page, SocialFields):
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES)
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text="The full bleed image in the background")
    head_of_school = models.ForeignKey('rca.StaffPage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    head_of_school_statement = RichTextField(null=True, blank=True)
    head_of_school_link = models.ForeignKey('core.Page', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=TWITTER_FEED_HELP_TEXT)
    contact_title = models.CharField(max_length=255, blank=True)
    contact_address = models.TextField(blank=True)
    contact_link = models.URLField(blank=True)
    contact_link_text = models.CharField(max_length=255, blank=True)
    head_of_research = models.ForeignKey('rca.StaffPage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    head_of_research_statement = RichTextField(null=True, blank=True)
    head_of_research_link = models.ForeignKey('core.Page', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    indexed_fields = ('get_school_display', )

    search_name = 'School'

SchoolPage.content_panels = [
    FieldPanel('title', classname="full title"),
    ImageChooserPanel('background_image'),
    InlinePanel(SchoolPage, 'carousel_items', label="Carousel content", help_text="test"),
    PageChooserPanel('head_of_school', 'rca.StaffPage'),
    FieldPanel('head_of_school_statement', classname="full"),
    PageChooserPanel('head_of_school_link'),
    FieldPanel('twitter_feed'),
    MultiFieldPanel([
        FieldPanel('contact_title'),
        FieldPanel('contact_address'),
        FieldPanel('contact_link'),
        FieldPanel('contact_link_text'),
    ], 'Contact'),
    InlinePanel(SchoolPage, 'contact_tel_email', label="Contact phone numbers/emails"),
    InlinePanel(SchoolPage, 'contact_phone', label="Contact phone number"),
    InlinePanel(SchoolPage, 'contact_email', label="Contact email"),
    PageChooserPanel('head_of_research', 'rca.StaffPage'),
    FieldPanel('head_of_research_statement', classname="full"),
    PageChooserPanel('head_of_research_link'),
    InlinePanel(SchoolPage, 'related_links', label="Related links"),
    InlinePanel(SchoolPage, 'manual_adverts', label="Manual adverts"),
]

SchoolPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),

    FieldPanel('school'),
]


# == Programme page ==

class ProgrammePageCarouselItem(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='carousel_items')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    text = models.CharField(max_length=255, help_text='This text will overlay the image', blank=True)
    url = models.URLField(null=True, blank=True)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('text'),
        FieldPanel('url'),
    ]

class ProgrammePageManualStaffFeed(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='manual_staff_feed')
    staff = models.ForeignKey('rca.StaffPage', null=True, blank=True, related_name='+')
    staff_role = models.CharField(max_length=255, blank=True)

    panels = [
        PageChooserPanel('staff', 'rca.StaffPage'),
        FieldPanel('staff_role'),
    ]

class ProgrammePageRelatedLink(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='related_links')
    link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    link_text = models.CharField(max_length=255, help_text="Alternative link title (default is target page's title)")

    panels = [
        PageChooserPanel('link'),
        FieldPanel('link_text'),
    ]

class ProgrammePageContactPhone(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='contact_phone')
    phone_number = models.CharField(max_length=255)

    panels = [
        FieldPanel('phone_number')
    ]

class ProgrammePageContactEmail(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='contact_email')
    email_address = models.CharField(max_length=255)

    panels = [
        FieldPanel('email_address')
    ]

class ProgrammePageOurSites(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='our_sites')
    url = models.URLField()
    site_name = models.CharField(max_length=255)
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('url'),
        FieldPanel('site_name')
    ]

class ProgrammeDocuments(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='documents')
    document = models.ForeignKey('verdantdocs.Document', null=True, blank=True, related_name='+')
    text = models.CharField(max_length=255, blank=True)

    panels = [
        DocumentChooserPanel('document'),
        FieldPanel('text')
    ]

class ProgrammePageStudentStory(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='student_stories')
    name = models.CharField(max_length=255)
    text = RichTextField()
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    link = models.ForeignKey('core.Page', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    panels = [
        FieldPanel('name'),
        FieldPanel('text'),
        ImageChooserPanel('image'),
        PageChooserPanel('link'),
    ]

class ProgrammePageAd(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+')

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class ProgrammePage(Page, SocialFields):
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES)
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES)
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text="The full bleed image in the background")
    head_of_programme = models.ForeignKey('rca.StaffPage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text="This is my help text")
    head_of_programme_statement = RichTextField(null=True, blank=True, help_text="This is my content this is my content this is my content")
    head_of_programme_link = models.ForeignKey('core.Page', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    programme_video = models.CharField(max_length=255, blank=True)
    programme_video_poster_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=TWITTER_FEED_HELP_TEXT)
    contact_title = models.CharField(max_length=255, blank=True)
    contact_address = models.TextField(blank=True)
    contact_link = models.URLField(blank=True)
    contact_link_text = models.CharField(max_length=255, blank=True)
    download_document_url = models.CharField(max_length=255, blank=True)
    download_document_text = models.CharField(max_length=255, blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term")
    facilities_text = RichTextField(null=True, blank=True)
    facilities_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    facilities_link = models.ForeignKey('core.Page', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    indexed_fields = ('get_programme_display', 'get_school_display')

    search_name = 'Programme'

    def tabbed_feature_count(self):
        count = 0;
        if self.programme_video:
            count = count + 1;
        if self.facilities_text or self.facilities_image:
            count = count + 1;
        if self.student_stories.exists():
            count = count + 1;
        return count;

ProgrammePage.content_panels = [
    ImageChooserPanel('background_image'),
    FieldPanel('title', classname="full title"),
    InlinePanel(ProgrammePage, 'carousel_items', label="Carousel content"),
    InlinePanel(ProgrammePage, 'related_links', label="Related links"),
    PageChooserPanel('head_of_programme', 'rca.StaffPage'),
    FieldPanel('head_of_programme_statement'),
    PageChooserPanel('head_of_programme_link'),
    InlinePanel(ProgrammePage, 'manual_staff_feed', label="Manual staff feed"),
    InlinePanel(ProgrammePage, 'our_sites', label="Our sites"),
    MultiFieldPanel([
        FieldPanel('programme_video'),
        ImageChooserPanel('programme_video_poster_image'),
    ], 'Video'),
    InlinePanel(ProgrammePage, 'student_stories', label="Student stories"),
    MultiFieldPanel([
        ImageChooserPanel('facilities_image'),
        FieldPanel('facilities_text'),
        PageChooserPanel('facilities_link'),
    ], 'Facilities'),
    InlinePanel(ProgrammePage, 'documents', label="Documents"),
    InlinePanel(ProgrammePage, 'manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
    MultiFieldPanel([
        FieldPanel('contact_title'),
        FieldPanel('contact_address'),
        FieldPanel('contact_link'),
        FieldPanel('contact_link_text'),
    ], 'Contact'),
    InlinePanel(ProgrammePage, 'contact_phone', label="Contact phone number"),
    InlinePanel(ProgrammePage, 'contact_email', label="Contact email"),
]

ProgrammePage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),

    FieldPanel('school'),
    FieldPanel('programme'),
]


# == News Index ==

class NewsIndexAd(Orderable):
    page = ParentalKey('rca.NewsIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+')

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class NewsIndex(Page, SocialFields):
    intro = RichTextField(blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=TWITTER_FEED_HELP_TEXT)
    subpage_types = ['NewsItem']

    indexed = False

    def serve(self, request):
        programme = request.GET.get('programme')
        school = request.GET.get('school')
        area = request.GET.get('area')

        news = NewsItem.objects.filter(live=True, path__startswith=self.path)

        if programme:
            news = news.filter(related_programmes__programme=programme)
        if school:
            news = news.filter(related_schools__school=school)
        if area:
            news = news.filter(area=area)

        news = news.distinct().order_by('-date')

        related_programmes = SCHOOL_PROGRAMME_MAP[school] if school else []

        page = request.GET.get('page')
        paginator = Paginator(news, 10)  # Show 10 news items per page
        try:
            news = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            news = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            news = paginator.page(paginator.num_pages)

        if request.is_ajax():
            return render(request, "rca/includes/news_listing.html", {
                'self': self,
                'news': news,
                'related_programmes': related_programmes,
            })
        else:
            return render(request, self.template, {
                'self': self,
                'news': news,
            })

NewsIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel(NewsIndex, 'manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
]

NewsIndex.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]

# == News Item ==

class NewsItemCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.NewsItem', related_name='carousel_items')

class NewsItemLink(Orderable):
    page = ParentalKey('rca.NewsItem', related_name='related_links')
    link = models.URLField()
    link_text = models.CharField(max_length=255)

    panels=[
        FieldPanel('link'),
        FieldPanel('link_text')
    ]

class NewsItemRelatedSchool(models.Model):
    page = ParentalKey('rca.NewsItem', related_name='related_schools')
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True)

    panels = [
        FieldPanel('school')
    ]

class NewsItemRelatedProgramme(models.Model):
    page = ParentalKey('rca.NewsItem', related_name='related_programmes')
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True)

    panels = [FieldPanel('programme')]

class NewsItem(Page, SocialFields):
    author = models.CharField(max_length=255)
    date = models.DateField()
    intro = RichTextField()
    body = RichTextField()
    show_on_homepage = models.BooleanField()
    listing_intro = models.CharField(max_length=100, help_text='Used only on pages listing news items', blank=True)
    area = models.CharField(max_length=255, choices=AREA_CHOICES, blank=True)
    rca_content_id = models.CharField(max_length=255, blank=True) # for import
    # TODO: Embargo Date, which would perhaps be part of a workflow module, not really a model thing?

    indexed_fields = ('intro', 'body')

    search_name = 'News'

    def get_related_news(self, count=4):
        return NewsItem.get_related(
            area=self.area,
            programmes=list(self.related_programmes.values_list('programme', flat=True)),
            schools=list(self.related_schools.values_list('school', flat=True)),
            exclude=self,
            count=count
        )

    @staticmethod
    def get_related(area=None, programmes=None, schools=None, exclude=None, count=4):
        """
            Get NewsItem objects that have the highest relevance to the specified
            area (singular), programmes (multiple) and schools (multiple).
        """

        # Assign each news item a score indicating similarity to these params:
        # 100 points for a matching area, 10 points for a matching programme,
        # 1 point for a matching school.

        # if self.area is blank, we don't want to give priority to other news items
        # that also have a blank area field - so instead, set the target area to
        # something that will never match, so that it never contributes to the score
        area = area or "this_will_never_match"

        if not programmes:
            # insert a dummy programme name to avoid an empty IN clause
            programmes = ["this_will_never_match_either"]

        if not schools:
            # insert a dummy school name to avoid an empty IN clause
            schools = ["this_will_never_match_either"]

        results = NewsItem.objects.extra(
            select={'score': """
                CASE WHEN rca_newsitem.area = %s THEN 100 ELSE 0 END
                + (
                    SELECT COUNT(*) FROM rca_newsitemrelatedprogramme
                    WHERE rca_newsitemrelatedprogramme.page_id=core_page.id
                        AND rca_newsitemrelatedprogramme.programme IN %s
                ) * 10
                + (
                    SELECT COUNT(*) FROM rca_newsitemrelatedschool
                    WHERE rca_newsitemrelatedschool.page_id=core_page.id
                        AND rca_newsitemrelatedschool.school IN %s
                ) * 1
            """},
            select_params=(area, tuple(programmes), tuple(schools))
        )
        if exclude:
            results = results.exclude(id=exclude.id)

        return results.order_by('-score')[:count]


NewsItem.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('author'),
    FieldPanel('date'),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    InlinePanel(NewsItem, 'related_links', label="Links"),
    InlinePanel(NewsItem, 'carousel_items', label="Carousel content"),
]

NewsItem.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('show_on_homepage'),
        FieldPanel('listing_intro'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),

    FieldPanel('area'),
    InlinePanel(NewsItem, 'related_schools', label="Related schools"),
    InlinePanel(NewsItem, 'related_programmes', label="Related programmes"),
]

# == Press Release Index ==

class PressReleaseIndexAd(Orderable):
    page = ParentalKey('rca.PressReleaseIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+')

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class PressReleaseIndex(Page, SocialFields):
    intro = RichTextField(blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=TWITTER_FEED_HELP_TEXT)

    indexed = False

    def serve(self, request):
        press_releases = PressRelease.objects.filter(live=True)
        return render(request, self.template, {
            'self': self,
            'press_releases': press_releases,
        })


PressReleaseIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel(PressReleaseIndex, 'manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
]

PressReleaseIndex.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]


# == Press release Item ==

class PressReleaseCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.PressRelease', related_name='carousel_items')

class PressReleaseLink(Orderable):
    page = ParentalKey('rca.PressRelease', related_name='related_links')
    link = models.URLField()
    link_text = models.CharField(max_length=255)

    panels=[
        FieldPanel('link'),
        FieldPanel('link_text')
    ]

class PressReleaseRelatedSchool(models.Model):
    page = ParentalKey('rca.PressRelease', related_name='related_schools')
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True)

    panels = [
        FieldPanel('school')
    ]

class PressReleaseRelatedProgramme(models.Model):
    page = ParentalKey('rca.PressRelease', related_name='related_programmes')
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True)

    panels = [FieldPanel('programme')]

class PressRelease(Page, SocialFields):
    author = models.CharField(max_length=255)
    date = models.DateField()
    intro = RichTextField()
    body = RichTextField()
    show_on_homepage = models.BooleanField()
    listing_intro = models.CharField(max_length=100, help_text='Used only on pages listing news items', blank=True)
    area = models.CharField(max_length=255, choices=AREA_CHOICES, blank=True)
    # TODO: Embargo Date, which would perhaps be part of a workflow module, not really a model thing?

    indexed_fields = ('intro', 'body')

    search_name = 'PressRelease'


PressRelease.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('author'),
    FieldPanel('date'),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    InlinePanel(PressRelease, 'related_links', label="Links"),
    InlinePanel(PressRelease, 'carousel_items', label="Carousel content"),
]

PressRelease.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('show_on_homepage'),
        FieldPanel('listing_intro'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),

    FieldPanel('area'),
    InlinePanel(PressRelease, 'related_schools', label="Related schools"),
    InlinePanel(PressRelease, 'related_programmes', label="Related programmes"),
]


# == Event Item ==

class EventItemSpeaker(Orderable):
    page = ParentalKey('rca.EventItem', related_name='speakers')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)
    link = models.URLField(blank=True)

    panels=[
        FieldPanel('name'),
        FieldPanel('surname'),
        ImageChooserPanel('image'),
        FieldPanel('link'),
    ]


class EventItemCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.EventItem', related_name='carousel_items')

class EventItemRelatedSchool(models.Model):
    page = ParentalKey('rca.EventItem', related_name='related_schools')
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True)

    panels = [FieldPanel('school')]

class EventItemRelatedProgramme(models.Model):
    page = ParentalKey('rca.EventItem', related_name='related_programmes')
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True)

    panels = [FieldPanel('programme')]

class EventItemRelatedArea(models.Model):
    page = ParentalKey('rca.EventItem', related_name='related_areas')
    area = models.CharField(max_length=255, choices=AREA_CHOICES, blank=True)

    panels = [FieldPanel('area')]

class EventItemContactPhone(Orderable):
    page = ParentalKey('rca.EventItem', related_name='contact_phone')
    phone_number = models.CharField(max_length=255)

    panels = [
        FieldPanel('phone_number')
    ]

class EventItemContactEmail(Orderable):
    page = ParentalKey('rca.EventItem', related_name='contact_email')
    email_address = models.CharField(max_length=255)

    panels = [
        FieldPanel('email_address')
    ]

class EventItemDatesTimes(Orderable):
    page = ParentalKey('rca.EventItem', related_name='dates_times')
    date_from = models.DateField("Start date")
    date_to = models.DateField("End date", null=True, blank=True, help_text="Not required if event is on a single day")
    time_from = models.TimeField("Start time", null=True, blank=True)
    time_to = models.TimeField("End time", null=True, blank=True)
    time_other = models.CharField("Time other", max_length=255, blank=True, help_text='Use this field to give additional information about start and end times')

    panels = [
        FieldPanel('date_from'),
        FieldPanel('date_to'),
        FieldPanel('time_from'),
        FieldPanel('time_to'),
        FieldPanel('time_other'),
    ]

class FutureEventItemManager(models.Manager):
    def get_query_set(self):
        return super(FutureEventItemManager, self).get_query_set().extra(
            where=["core_page.id IN (SELECT DISTINCT page_id FROM rca_eventitemdatestimes WHERE date_from >= %s OR date_to >= %s)"],
            params=[date.today(), date.today()]
        )

class PastEventItemManager(models.Manager):
    def get_query_set(self):
        return super(PastEventItemManager, self).get_query_set().extra(
            where=["core_page.id NOT IN (SELECT DISTINCT page_id FROM rca_eventitemdatestimes WHERE date_from >= %s OR date_to >= %s)"],
            params=[date.today(), date.today()]
        )

class EventItem(Page, SocialFields):
    body = RichTextField(blank=True)
    audience = models.CharField(max_length=255, choices=EVENT_AUDIENCE_CHOICES)
    area = models.CharField(max_length=255, choices=AREA_CHOICES, blank=True)
    location = models.CharField(max_length=255, choices=EVENT_LOCATION_CHOICES)
    location_other = models.CharField("'Other' location", max_length=255, blank=True)
    specific_directions = models.CharField(max_length=255, blank=True, help_text="Brief, more specific location e.g Go to reception on 2nd floor")
    specific_directions_link = models.URLField(blank=True)
    gallery = models.CharField(max_length=255, choices=EVENT_GALLERY_CHOICES, blank=True)
    cost = RichTextField(blank=True, help_text="Prices should be in bold")
    eventbrite_id = models.CharField(max_length=255, blank=True, help_text='Must be a ten-digit number. You can find for you event ID by logging on to Eventbrite, then going to the Manage page for your event. Once on the Manage page, look in the address bar of your browser for eclass=XXXXXXXXXX. This ten-digit number after eclass= is the event ID.')
    external_link = models.URLField(blank=True)
    external_link_text = models.CharField(max_length=255, blank=True)
    show_on_homepage = models.BooleanField()
    listing_intro = models.CharField(max_length=100, help_text='Used only on pages listing event items', blank=True)
    middle_column_body = RichTextField(blank=True)
    contact_title = models.CharField(max_length=255, blank=True)
    contact_address = models.TextField(blank=True)
    contact_link = models.URLField(blank=True)
    contact_link_text = models.CharField(max_length=255, blank=True)
    # TODO: Embargo Date, which would perhaps be part of a workflow module, not really a model thing?

    objects = models.Manager()
    future_objects = FutureEventItemManager()
    past_objects = PastEventItemManager()

    indexed_fields = ('body', 'get_location_display', 'location_other')

    search_name = 'Event'

    def serve(self, request):
        if "format" in request.GET:
            if request.GET['format'] == 'ical':
                # Begin event
                # VEVENT format: http://www.kanzaki.com/docs/ical/vevent.html
                ical_components = [
                    'BEGIN:VCALENDAR',
                    'VERSION:2.0',
                    'PRODID:-//Torchbox//verdant//EN',
                ]

                for eventdate in self.dates_times.all():
                    # Work out number of days the event lasts
                    if eventdate.date_to is not None:
                        days = (eventdate.date_to - eventdate.date_from).days + 1
                    else:
                        days = 1

                    for day in range(days):
                        # Get date
                        date = eventdate.date_from + datetime.timedelta(days=day)

                        # Get times
                        if eventdate.time_from is not None:
                            start_time = eventdate.time_from
                        else:
                            start_time = datetime.time.min
                        if eventdate.time_to is not None:
                            end_time = eventdate.time_to
                        else:
                            end_time = datetime.time.max

                        # Combine dates and times
                        start_datetime = datetime.datetime.combine(date, start_time)
                        end_datetime = datetime.datetime.combine(date, end_time)

                        # Get location
                        if self.location == "other":
                            location = self.location_other
                        else:
                            location = self.get_location_display()

                        def add_slashes(string):
                            string.replace('"', '\\"')
                            string.replace('\\', '\\\\')
                            string.replace(',', '\\,')
                            string.replace(':', '\\:')
                            string.replace(';', '\\;')
                            string.replace('\n', '\\n')
                            return string

                        # Make event
                        ical_components.extend([
                            'BEGIN:VEVENT',
                            'UID:' + add_slashes(self.url) + str(day + 1),
                            'URL:' + add_slashes(self.url),
                            'DTSTAMP:' + start_time.strftime('%Y%m%dT%H%M%S'),
                            'SUMMARY:' + add_slashes(self.title),
                            'DESCRIPTION:' + add_slashes(self.body),
                            'LOCATION:' + add_slashes(location),
                            'DTSTART;TZID=Europe/London:' + start_datetime.strftime('%Y%m%dT%H%M%S'),
                            'DTEND;TZID=Europe/London:' + end_datetime.strftime('%Y%m%dT%H%M%S'),
                            'END:VEVENT',
                        ])

                # Finish event
                ical_components.extend([
                    'END:VCALENDAR'
                ])

                # Send response
                response = HttpResponse("\r".join(ical_components), content_type='text/calendar')
                response['Content-Disposition'] = 'attachment; filename=' + self.slug + '.ics'
                return response
            else:
                # Unrecognised format error
                message = 'Could not export event\n\nUnrecognised format: ' + request.GET['format']
                return HttpResponse(message, content_type='text/plain')
        else:
            # Display event page as usual
            return super(EventItem, self).serve(request)

EventItem.content_panels = [
    MultiFieldPanel([
        FieldPanel('title', classname="full title"),
        FieldPanel('audience'),
        FieldPanel('area'),
        FieldPanel('location'),
        FieldPanel('location_other'),
        FieldPanel('specific_directions'),
        FieldPanel('specific_directions_link'),
        FieldPanel('gallery'),
        FieldPanel('cost'),
        FieldPanel('eventbrite_id'),
        FieldPanel('external_link'),
        FieldPanel('external_link_text'),
        FieldPanel('middle_column_body')
    ], 'Event detail'),
    FieldPanel('body', classname="full"),
    InlinePanel(EventItem, 'dates_times', label="Dates and times"),
    InlinePanel(EventItem, 'speakers', label="Speaker"),
    InlinePanel(EventItem, 'carousel_items', label="Carousel content"),
    MultiFieldPanel([
        FieldPanel('contact_title'),
        FieldPanel('contact_address'),
        FieldPanel('contact_link'),
        FieldPanel('contact_link_text'),
    ],'Contact'),
    InlinePanel(EventItem, 'contact_phone', label="Contact phone number"),
    InlinePanel(EventItem, 'contact_email', label="Contact email address"),
]

EventItem.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('show_on_homepage'),
        FieldPanel('listing_intro'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),

    InlinePanel(EventItem, 'related_schools', label="Related schools"),
    InlinePanel(EventItem, 'related_programmes', label="Related programmes"),
    InlinePanel(EventItem, 'related_areas', label="Related areas"),
]


# == Event index ==

class EventIndexRelatedLink(Orderable):
    page = ParentalKey('rca.EventIndex', related_name='related_links')
    link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    link_text = models.CharField(max_length=255, help_text="Alternative link title (default is target page's title)")

    panels = [
        PageChooserPanel('link'),
        FieldPanel('link_text'),
    ]

class EventIndexAd(Orderable):
    page = ParentalKey('rca.EventIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+')

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class EventIndex(Page, SocialFields):
    intro = RichTextField(blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=TWITTER_FEED_HELP_TEXT)

    indexed = False

    def future_events(self):
        return EventItem.future_objects.filter(live=True, path__startswith=self.path)

    def past_events(self):
        return EventItem.past_objects.filter(live=True, path__startswith=self.path)

    def serve(self, request):
        programme = request.GET.get('programme')
        school = request.GET.get('school')
        location = request.GET.get('location')
        location_other = request.GET.get('location_other')
        area = request.GET.get('area')
        audience = request.GET.get('audience')
        period = request.GET.get('period')

        if period == 'past':
            events = self.past_events()
        else:
            events = self.future_events()

        if programme and programme != '':
            events = events.filter(related_programmes__programme=programme)
        if school and school != 'all':
            events = events.filter(related_schools__school=school)
        if location and location != '':
            events = events.filter(location=location)
        if area and area != 'all':
            events = events.filter(related_areas__area=area)
        if audience and audience != '':
            events = events.filter(audience=audience)
        events = events.annotate(start_date=Min('dates_times__date_from')).order_by('start_date')

        related_programmes = SCHOOL_PROGRAMME_MAP[school] if school else []

        page = request.GET.get('page')
        paginator = Paginator(events, 10)  # Show 10 events per page
        try:
            events = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            events = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            events = paginator.page(paginator.num_pages)

        if request.is_ajax():
            return render(request, "rca/includes/events_listing.html", {
                'self': self,
                'events': events
            })
        else:
            return render(request, self.template, {
                'self': self,
                'events': events,
                'related_programmes': related_programmes,
            })

EventIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel(EventIndex, 'related_links', label="Related links"),
    InlinePanel(EventIndex, 'manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
]

EventIndex.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]

# == Talks index ==


class TalksIndexAd(Orderable):
    page = ParentalKey('rca.TalksIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+')

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class TalksIndex(Page, SocialFields):
    intro = RichTextField(blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term")

    indexed = False

    def serve(self, request):
        talks = EventItem.past_objects.filter(live=True, audience='rcatalks').annotate(start_date=Min('dates_times__date_from')).order_by('start_date')

        talks = talks.distinct()

        page = request.GET.get('page')

        paginator = Paginator(talks, 6)  # Show 6 talks items per page
        try:
            talks = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            talks = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            talks = paginator.page(paginator.num_pages)

        if request.is_ajax():
            return render(request, "rca/includes/talks_listing.html", {
                'self': self,
                'talks': talks
            })
        else:
            return render(request, self.template, {
                'self': self,
                'talks': talks,
            })

TalksIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel(TalksIndex, 'manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
]

TalksIndex.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]



# == Reviews index ==


class ReviewsIndexAd(Orderable):
    page = ParentalKey('rca.ReviewsIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+')

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class ReviewsIndex(Page, SocialFields):
    intro = RichTextField(blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term")

    indexed = False

    def serve(self, request):
        reviews = ReviewPage.objects.filter(live=True)

        reviews = reviews.distinct()

        page = request.GET.get('page')

        paginator = Paginator(reviews, 10)  # Show 10 news items per page
        try:
            reviews = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            reviews = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            reviews = paginator.page(paginator.num_pages)

        if request.is_ajax():
            return render(request, "rca/includes/news_listing.html", {
                'self': self,
                'reviews': reviews
            })
        else:
            return render(request, self.template, {
                'self': self,
                'reviews': reviews,
            })

ReviewsIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel(ReviewsIndex, 'manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
]

ReviewsIndex.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]


# == Review page ==

class ReviewPageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.ReviewPage', related_name='carousel_items')

class ReviewPageRelatedLink(Orderable):
    page = ParentalKey('rca.ReviewPage', related_name='related_links')
    link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    link_text = models.CharField(max_length=255, help_text="Alternative link title (default is target page's title)")

    panels = [
        PageChooserPanel('link'),
        FieldPanel('link_text'),
    ]

class ReviewPageQuotation(Orderable):
    page = ParentalKey('rca.ReviewPage', related_name='quotations')
    quotation = models.TextField()
    quotee = models.CharField(max_length=255, blank=True)
    quotee_job_title = models.CharField(max_length=255, blank=True)

    panels = [
        FieldPanel('quotation'),
        FieldPanel('quotee'),
        FieldPanel('quotee_job_title')
    ]

class ReviewPageRelatedDocument(Orderable):
    page = ParentalKey('rca.ReviewPage', related_name='documents')
    document = models.ForeignKey('verdantdocs.Document', null=True, blank=True, related_name='+')
    document_name = models.CharField(max_length=255)

    panels = [
        DocumentChooserPanel('document'),
        FieldPanel('document_name')
    ]

class ReviewPageImage(Orderable):
    page = ParentalKey('rca.ReviewPage', related_name='images')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')

    panels = [
        ImageChooserPanel('image'),
    ]

class ReviewPageAd(Orderable):
    page = ParentalKey('rca.ReviewPage', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+')

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class ReviewPage(Page, SocialFields):
    intro = RichTextField(blank=True)
    body = RichTextField(blank=True)
    strapline = models.CharField(max_length=255, blank=True)
    middle_column_body = RichTextField(blank=True)
    author = models.CharField(max_length=255, blank=True)
    listing_intro = models.CharField(max_length=255, help_text='Used only on pages listing jobs', blank=True)
    show_on_homepage = models.BooleanField()

    indexed_fields = ('body', 'strapline', 'author')

    search_name = 'Review'

ReviewPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('strapline', classname="full"),
    FieldPanel('author'),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    InlinePanel(ReviewPage, 'carousel_items', label="Carousel content"),
    InlinePanel(ReviewPage, 'related_links', label="Related links"),
    FieldPanel('middle_column_body', classname="full"),
    InlinePanel(ReviewPage, 'documents', label="Document"),
    InlinePanel(ReviewPage, 'quotations', label="Quotation"),
    InlinePanel(ReviewPage, 'images', label="Middle column image"),
    InlinePanel(ReviewPage, 'manual_adverts', label="Manual adverts"),
]

ReviewPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('show_on_homepage'),
        ImageChooserPanel('feed_image'),
        FieldPanel('listing_intro'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]

# == Standard page ==

class StandardPageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.StandardPage', related_name='carousel_items')

class StandardPageRelatedLink(Orderable):
    page = ParentalKey('rca.StandardPage', related_name='related_links')
    link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    link_text = models.CharField(max_length=255, help_text="Alternative link title (default is target page's title)")

    panels = [
        PageChooserPanel('link'),
        FieldPanel('link_text'),
    ]

class StandardPageQuotation(Orderable):
    page = ParentalKey('rca.StandardPage', related_name='quotations')
    quotation = models.TextField()
    quotee = models.CharField(max_length=255, blank=True)
    quotee_job_title = models.CharField(max_length=255, blank=True)

    panels = [
        FieldPanel('quotation'),
        FieldPanel('quotee'),
        FieldPanel('quotee_job_title')
    ]

class StandardPageRelatedDocument(Orderable):
    page = ParentalKey('rca.StandardPage', related_name='documents')
    document = models.ForeignKey('verdantdocs.Document', null=True, blank=True, related_name='+')
    document_name = models.CharField(max_length=255)

    panels = [
        DocumentChooserPanel('document'),
        FieldPanel('document_name')
    ]

class StandardPageImage(Orderable):
    page = ParentalKey('rca.StandardPage', related_name='images')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')

    panels = [
        ImageChooserPanel('image'),
    ]

class StandardPageAd(Orderable):
    page = ParentalKey('rca.StandardPage', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+')

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class StandardPageReusableTextSnippet(Orderable):
    page = ParentalKey('rca.StandardPage', related_name='reusable_text_snippets')
    reusable_text_snippet = models.ForeignKey('rca.ReusableTextSnippet', related_name='+')

    panels = [
        SnippetChooserPanel('reusable_text_snippet', ReusableTextSnippet),
    ]

class StandardPage(Page, SocialFields):
    intro = RichTextField(blank=True)
    body = RichTextField(blank=True)
    strapline = models.CharField(max_length=255, blank=True)
    middle_column_body = RichTextField(blank=True)
    show_on_homepage = models.BooleanField()
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=TWITTER_FEED_HELP_TEXT)

    indexed_fields = ('intro', 'body')

    search_name = None

StandardPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('strapline', classname="full"),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    InlinePanel(StandardPage, 'carousel_items', label="Carousel content"),
    InlinePanel(StandardPage, 'related_links', label="Related links"),
    FieldPanel('middle_column_body', classname="full"),
    InlinePanel(StandardPage, 'reusable_text_snippets', label="Reusable text snippet"),
    InlinePanel(StandardPage, 'documents', label="Document"),
    InlinePanel(StandardPage, 'quotations', label="Quotation"),
    InlinePanel(StandardPage, 'images', label="Middle column image"),
    InlinePanel(StandardPage, 'manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
    ]

StandardPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('show_on_homepage'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]


# == Standard Index page ==

class StandardIndexCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.StandardIndex', related_name='carousel_items')

class StandardIndexTeaser(Orderable):
    page = ParentalKey('rca.StandardIndex', related_name='teasers')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    link = models.ForeignKey('core.Page', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    title = models.CharField(max_length=255, blank=True)
    text = models.CharField(max_length=255, blank=True)

    panels = [
        ImageChooserPanel('image'),
        PageChooserPanel('link'),
        FieldPanel('title', classname="full title"),
        FieldPanel('text'),
    ]

class StandardIndexRelatedLink(Orderable):
    page = ParentalKey('rca.StandardIndex', related_name='related_links')
    link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    link_text = models.CharField(max_length=255, help_text="Alternative link title (default is target page's title)")

    panels = [
        PageChooserPanel('link'),
        FieldPanel('link_text'),
    ]

class StandardIndexContactPhone(Orderable):
    page = ParentalKey('rca.StandardIndex', related_name='contact_phone')
    phone_number = models.CharField(max_length=255)

    panels = [
        FieldPanel('phone_number')
    ]

class StandardIndexContactEmail(Orderable):
    page = ParentalKey('rca.StandardIndex', related_name='contact_email')
    email_address = models.CharField(max_length=255)

    panels = [
        FieldPanel('email_address')
    ]

class StandardIndexOurSites(Orderable):
    page = ParentalKey('rca.StandardIndex', related_name='our_sites')
    url = models.URLField()
    site_name = models.CharField(max_length=255)
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('url'),
        FieldPanel('site_name')
    ]

class StandardIndexAd(Orderable):
    page = ParentalKey('rca.StandardIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+')

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class StandardIndexCustomContentModules(Orderable):
    page = ParentalKey('rca.StandardIndex', related_name='custom_content_modules')
    custom_content_module = models.ForeignKey('rca.CustomContentModule', related_name='+')

    panels = [
        SnippetChooserPanel('custom_content_module', CustomContentModule),
    ]

class StandardIndexContactSnippet(Orderable):
    page = ParentalKey('rca.StandardIndex', related_name='contact_snippets')
    contact_snippet = models.ForeignKey('rca.ContactSnippet', related_name='+')

    panels = [
        SnippetChooserPanel('contact_snippet', ContactSnippet),
    ]

class StandardIndex(Page, SocialFields):
    intro = RichTextField(blank=True)
    intro_link = models.ForeignKey('core.Page', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    strapline = models.CharField(max_length=255, blank=True)
    body = RichTextField(blank=True)
    teasers_title = models.CharField(max_length=255, blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=TWITTER_FEED_HELP_TEXT)
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text="The full bleed image in the background")
    contact_title = models.CharField(max_length=255, blank=True)
    contact_address = models.TextField(blank=True)
    contact_link = models.URLField(blank=True)
    contact_link_text = models.CharField(max_length=255, blank=True)
    news_carousel_area = models.CharField(max_length=255, choices=AREA_CHOICES, blank=True)
    staff_feed_source = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True)
    show_events_feed = models.BooleanField(default=False)
    events_feed_area = models.CharField(max_length=255, choices=AREA_CHOICES, blank=True)

    indexed = False

StandardIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('strapline', classname="full"),
    ImageChooserPanel('background_image'),
    MultiFieldPanel([
        FieldPanel('intro', classname="full"),
        PageChooserPanel('intro_link'),
    ],'Introduction'),
    FieldPanel('body'),
    InlinePanel(StandardIndex, 'carousel_items', label="Carousel content"),
    FieldPanel('teasers_title'),
    InlinePanel(StandardIndex, 'teasers', label="Teaser content"),
    InlinePanel(StandardIndex, 'custom_content_modules', label="Modules"),
    InlinePanel(StandardIndex, 'our_sites', label="Our sites"),
    InlinePanel(StandardIndex, 'related_links', label="Related links"),
    InlinePanel(StandardIndex, 'manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
    MultiFieldPanel([
        FieldPanel('contact_title'),
        FieldPanel('contact_address'),
        FieldPanel('contact_link'),
        FieldPanel('contact_link_text'),
    ],'Contact'),
    InlinePanel(StandardIndex, 'contact_snippets', label="Contacts"),
    InlinePanel(StandardIndex, 'contact_phone', label="Contact phone number"),
    InlinePanel(StandardIndex, 'contact_email', label="Contact email address"),
    FieldPanel('staff_feed_source'),
    FieldPanel('news_carousel_area'),
    MultiFieldPanel([
        FieldPanel('show_events_feed'),
        FieldPanel('events_feed_area'),
        ],'Events feed')
]

StandardIndex.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]


# == Home page ==

class HomePageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.HomePage', related_name='carousel_items')

class HomePageAd(Orderable):
    page = ParentalKey('rca.HomePage', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+')

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class HomePage(Page, SocialFields):
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text="The full bleed image in the background")
    news_item_1 = models.ForeignKey('core.Page', null=True, on_delete=models.SET_NULL, related_name='+')
    news_item_2 = models.ForeignKey('core.Page', null=True, on_delete=models.SET_NULL, related_name='+')
    packery_news = models.IntegerField("Number of news items to show", null=True, blank=True, choices=((1,1),(2,2),(3,3),(4,4),(5,5),))
    packery_staff = models.IntegerField("Number of staff to show", null=True, blank=True, choices=((1,1),(2,2),(3,3),(4,4),(5,5),))
    packery_student_work = models.IntegerField("Number of student work items to show", help_text="Student pages flagged to Show On Homepage must have at least one carousel item", null=True, blank=True, choices=((1,1),(2,2),(3,3),(4,4),(5,5),))
    packery_tweets = models.IntegerField("Number of tweets to show", null=True, blank=True, choices=((1,1),(2,2),(3,3),(4,4),(5,5),))
    packery_rcanow = models.IntegerField("Number of RCA Now items to show", null=True, blank=True, choices=((1,1),(2,2),(3,3),(4,4),(5,5),))
    packery_standard = models.IntegerField("Number of standard pages to show", null=True, blank=True, choices=((1,1),(2,2),(3,3),(4,4),(5,5),))
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=TWITTER_FEED_HELP_TEXT)

HomePage.content_panels = [
    FieldPanel('title', classname="full title"),
    ImageChooserPanel('background_image'),
    InlinePanel(HomePage, 'carousel_items', label="Carousel content"),
    PageChooserPanel('news_item_1'),
    PageChooserPanel('news_item_2'),
    MultiFieldPanel([
        FieldPanel('packery_news'),
        FieldPanel('packery_staff'),
        FieldPanel('packery_student_work'),
        FieldPanel('packery_tweets'),
        FieldPanel('twitter_feed'),
        FieldPanel('packery_rcanow'),
        FieldPanel('packery_standard'),
    ], 'Packery content'),
    InlinePanel(HomePage, 'manual_adverts', label="Manual adverts"),
]

HomePage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]


# == Job page ==

class JobPageReusableTextSnippet(Orderable):
    page = ParentalKey('rca.JobPage', related_name='reusable_text_snippets')
    reusable_text_snippet = models.ForeignKey('rca.ReusableTextSnippet', related_name='+')

    panels = [
        SnippetChooserPanel('reusable_text_snippet', ReusableTextSnippet),
    ]

class JobPage(Page, SocialFields):
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, null=True, blank=True)
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, null=True, blank=True)
    other_department = models.CharField(max_length=255, blank=True)
    closing_date = models.DateField()
    interview_date = models.DateField(null=True, blank=True)
    responsible_to = models.CharField(max_length=255, blank=True)
    required_hours = models.CharField(max_length=255, blank=True)
    campus = models.CharField(max_length=255, choices=CAMPUS_CHOICES, null=True, blank=True)
    salary = models.CharField(max_length=255, blank=True)
    ref_number = models.CharField(max_length=255, blank=True)
    grade = models.CharField(max_length=255, blank=True)
    description = RichTextField()
    download_info = models.ForeignKey('verdantdocs.Document', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    listing_intro = models.CharField(max_length=255, help_text='Used only on pages listing jobs', blank=True)
    show_on_homepage = models.BooleanField()

    indexed_fields = ('get_programme_display', 'get_school_display', 'other_department', 'get_campus_display', 'description')

    search_name = 'Job'

JobPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('programme'),
    FieldPanel('school'),
    FieldPanel('other_department'),
    FieldPanel('closing_date'),
    FieldPanel('interview_date'),
    FieldPanel('responsible_to'),
    FieldPanel('required_hours'),
    FieldPanel('campus'),
    FieldPanel('salary'),
    FieldPanel('ref_number'),
    FieldPanel('grade'),
    FieldPanel('description', classname="full"),
    DocumentChooserPanel('download_info'),
    InlinePanel(StandardPage, 'reusable_text_snippets', label="Application and equal opportunities monitoring form text"),
]

JobPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('show_on_homepage'),
        FieldPanel('listing_intro'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]


# == Jobs index page ==

class JobsIndexRelatedLink(Orderable):
    page = ParentalKey('rca.JobsIndex', related_name='related_links')
    link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    link_text = models.CharField(max_length=255, help_text="Alternative link title (default is target page's title)")

    panels = [
        PageChooserPanel('link'),
        FieldPanel('link_text'),
    ]

class JobsIndexAd(Orderable):
    page = ParentalKey('rca.JobsIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+')

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class JobsIndex(Page, SocialFields):
    intro = RichTextField(blank=True)
    body = RichTextField(blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=TWITTER_FEED_HELP_TEXT)

    indexed = False

JobsIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    FieldPanel('body'),
    InlinePanel(JobsIndex, 'related_links', label="Related links"),
    InlinePanel(JobsIndex, 'manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
]

JobsIndex.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]



# == Alumni index page ==

class AlumniIndexRelatedLink(Orderable):
    page = ParentalKey('rca.AlumniIndex', related_name='related_links')
    link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    link_text = models.CharField(max_length=255, help_text="Alternative link title (default is target page's title)")

    panels = [
        PageChooserPanel('link'),
        FieldPanel('link_text'),
    ]

class AlumniIndexAd(Orderable):
    page = ParentalKey('rca.AlumniIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+')

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class AlumniIndex(Page, SocialFields):
    intro = RichTextField(blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=TWITTER_FEED_HELP_TEXT)


    indexed = False

    def serve(self, request):
        school = request.GET.get('school')
        programme = request.GET.get('programme')

        alumni_pages = AlumniPage.objects.filter(live=True)

        if school and school != '':
            alumni_pages = alumni_pages.filter(school=school)
        if programme and programme != '':
            alumni_pages = alumni_pages.filter(programme=programme)

        #alumni_pages = alumni_pages.distinct()
        alumni_pages = alumni_pages.order_by('?');

        # research_items.order_by('-year')

        related_programmes = SCHOOL_PROGRAMME_MAP[school] if school else []

        page = request.GET.get('page')
        paginator = Paginator(alumni_pages, 11)  # Show 8 research items per page
        try:
            staff_pages = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            staff_pages = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            staff_pages = paginator.page(paginator.num_pages)

        if request.is_ajax():
            return render(request, "rca/includes/alumni_pages_listing.html", {
                'self': self,
                'alumni_pages': alumni_pages,
                'related_programmes': related_programmes,
            })
        else:
            return render(request, self.template, {
                'self': self,
                'alumni_pages': alumni_pages
            })


AlumniIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel(AlumniIndex, 'related_links', label="Related links"),
    InlinePanel(AlumniIndex, 'manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
]

AlumniIndex.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]


# == Alumni profile page ==

class AlumniPage(Page, SocialFields):
    profile_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES)
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES)
    year = models.CharField(max_length=4, blank=True)
    intro = RichTextField(blank=True)
    listing_intro = models.CharField(max_length=100, help_text='Used only on pages displaying a list of pages of this type', blank=True)
    biography = RichTextField()
    show_on_homepage = models.BooleanField()

    indexed_fields = ('get_school_display', 'get_programme_display', 'intro', 'biography')

    search_name = 'Alumni'

AlumniPage.content_panels = [
    FieldPanel('title', classname="full title"),
    ImageChooserPanel('profile_image'),
    FieldPanel('school'),
    FieldPanel('programme'),
    FieldPanel('year'),
    FieldPanel('intro', classname="full"),
    FieldPanel('biography', classname="full"),
]

AlumniPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('show_on_homepage'),
        ImageChooserPanel('feed_image'),
        FieldPanel('listing_intro'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]

# == Staff profile page ==

class StaffPageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.StaffPage', related_name='carousel_items')

class StaffPageRole(Orderable):
    page = ParentalKey('rca.StaffPage', related_name='roles')
    title = models.CharField(max_length=255)
    school = models.CharField(max_length=255, blank=True, choices=SCHOOL_CHOICES)
    programme = models.CharField(max_length=255, blank=True, choices=PROGRAMME_CHOICES)
    area = models.CharField(max_length=255, blank=True, choices=AREA_CHOICES)
    email = models.EmailField(max_length=255)

    panels = [
        FieldPanel('title'),
        FieldPanel('school'),
        FieldPanel('programme'),
        FieldPanel('area'),
        FieldPanel('email'),
    ]

class StaffPageCollaborations(Orderable):
    page = ParentalKey('rca.StaffPage', related_name='collaborations')
    title = models.CharField(max_length=255)
    link = models.URLField()
    text = RichTextField(blank=True)
    date = models.CharField(max_length=255, blank=True)

    panels = [
        FieldPanel('title'),
        FieldPanel('link'),
        FieldPanel('text'),
        FieldPanel('date'),
    ]

class StaffPagePublicationExhibition(Orderable):
    page = ParentalKey('rca.StaffPage', related_name='publications_exhibitions')
    title = models.CharField(max_length=255)
    typeof = models.CharField("Type", max_length=255, choices=[('publication', 'Publication'),('exhibition', 'Exhibition')])
    location_year = models.CharField("Location and year", max_length=255)
    authors_collaborators = models.TextField("Authors/collaborators", blank=True)
    link = models.URLField(blank=True)
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    rca_content_id = models.CharField(max_length=255, blank=True) # for import

    panels = [
        FieldPanel('title'),
        FieldPanel('typeof'),
        FieldPanel('location_year'),
        FieldPanel('authors_collaborators'),
        FieldPanel('link'),
        ImageChooserPanel('image'),
    ]

class StaffPage(Page, SocialFields):
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES)
    profile_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    staff_type = models.CharField(max_length=255, blank=True, choices=STAFF_TYPES_CHOICES)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=TWITTER_FEED_HELP_TEXT)
    intro = RichTextField()
    biography = RichTextField(blank=True)
    practice = RichTextField(blank=True)
    publications_exhibtions_and_other_outcomes_placeholder = RichTextField(blank=True, help_text="This is a placeholder field for data import. Individual items can be split out into seperate publications/events if needed.")
    external_collaborations_placeholder = RichTextField(blank=True, help_text="This is a placeholder field for data import. Individual items can be split out into seperate external collaborations if needed.")
    current_recent_research = RichTextField(blank=True)
    awards_and_grants = RichTextField(blank=True)
    show_on_homepage = models.BooleanField()
    show_on_programme_page = models.BooleanField()
    listing_intro = models.CharField(max_length=100, help_text='Used only on pages displaying a list of pages of this type', blank=True)
    research_interests = RichTextField(blank=True)
    title_prefix = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    supervised_student_other = models.CharField(max_length=255, blank=True, help_text='Enter names of research students here who don\'t have a student profile. Supervised students with profile pages are pulled in automatically.')
    rca_content_id = models.CharField(max_length=255, blank=True) # for import

    indexed_fields = ('get_school_display', 'get_staff_type_display', 'intro', 'biography')

    search_name = 'Staff'

    def tabbed_feature_count(self):
        count = 2 #info tab and research tab will always show
        if self.carousel_items.exists():
            count = count + 1
        if self.publications_exhibitions.exists():
            count = count + 1
        return count

StaffPage.content_panels = [
    FieldPanel('title', classname="full title"),
    MultiFieldPanel([
        FieldPanel('title_prefix'),
        FieldPanel('first_name'),
        FieldPanel('last_name'),
    ], 'Full name'),
    FieldPanel('school'),
    ImageChooserPanel('profile_image'),
    FieldPanel('staff_type'),
    InlinePanel(StaffPage, 'roles', label="Roles"),
    FieldPanel('intro', classname="full"),
    FieldPanel('biography', classname="full"),
    FieldPanel('practice'),
    FieldPanel('publications_exhibtions_and_other_outcomes_placeholder'),
    FieldPanel('external_collaborations_placeholder'),
    FieldPanel('current_recent_research'),
    FieldPanel('awards_and_grants'),
    FieldPanel('twitter_feed'),
    FieldPanel('research_interests', classname="full"),
    FieldPanel('supervised_student_other'),

    InlinePanel(StaffPage, 'carousel_items', label="Selected Work Carousel Content"),
    InlinePanel(StaffPage, 'collaborations', label="Collaborations"),
    InlinePanel(StaffPage, 'publications_exhibitions', label="Publications and Exhibitions"),
]

StaffPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('show_on_homepage'),
        FieldPanel('show_on_programme_page'),
        FieldPanel('listing_intro'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]

# == Staff index page ==

class StaffIndexAd(Orderable):
    page = ParentalKey('rca.StaffIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+')

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class StaffIndex(Page, SocialFields):
    intro = RichTextField(blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=TWITTER_FEED_HELP_TEXT)

    indexed = False

    def serve(self, request):
        staff_type = request.GET.get('staff_type')
        school = request.GET.get('school')
        programme = request.GET.get('programme')
        area = request.GET.get('area')

        staff_pages = StaffPage.objects.filter(live=True)

        if staff_type and staff_type != '':
            staff_pages = staff_pages.filter(staff_type=staff_type)
        if school and school != '':
            staff_pages = staff_pages.filter(roles__school=school)
        if programme and programme != '':
            staff_pages = staff_pages.filter(roles__programme=programme)
        if area and area != '':
            staff_pages = staff_pages.filter(roles__area=area)

        # staff_pages = staff_pages.distinct()
        staff_pages = staff_pages.order_by('?')

        related_programmes = SCHOOL_PROGRAMME_MAP[school] if school else []

        # research_items.order_by('-year')

        page = request.GET.get('page')
        paginator = Paginator(staff_pages, 17)  # Show 11 research items per page
        try:
            staff_pages = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            staff_pages = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            staff_pages = paginator.page(paginator.num_pages)

        if request.is_ajax():
            return render(request, "rca/includes/staff_pages_listing.html", {
                'self': self,
                'staff_pages': staff_pages,
                'related_programmes': related_programmes,
            })
        else:
            return render(request, self.template, {
                'self': self,
                'staff_pages': staff_pages
            })

StaffIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel(StaffIndex, 'manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
]

StaffIndex.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]

# == Research student index ==

class ResearchStudentIndexAd(Orderable):
    page = ParentalKey('rca.ResearchStudentIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+')

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class ResearchStudentIndex(Page, SocialFields):
    intro = RichTextField(blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term")

    def serve(self, request):
        school = request.GET.get('school')
        programme = request.GET.get('programme')

        research_students = StudentPage.objects.filter(live=True, degree_qualification='researchstudent')

        if school and school != '':
            research_students = research_students.filter(roles__school=school)
        if programme and programme != '':
            research_students = research_students.filter(roles__programme=programme)

        research_students = research_students.distinct()

        related_programmes = SCHOOL_PROGRAMME_MAP[school] if school else []

        # research_items.order_by('-year')

        page = request.GET.get('page')
        paginator = Paginator(research_students, 17)  # Show 17 research students per page
        try:
            research_students = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            research_students = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            research_students = paginator.page(paginator.num_pages)

        if request.is_ajax():
            return render(request, "rca/includes/research_students_listing.html", {
                'self': self,
                'research_students': research_students,
                'related_programmes': related_programmes,
            })
        else:
            return render(request, self.template, {
                'self': self,
                'research_students': research_students
            })


ResearchStudentIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel(StaffIndex, 'manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
]

ResearchStudentIndex.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]




# == Student profile page ==

class StudentPageDegree(Orderable):
    page = ParentalKey('rca.StudentPage', related_name='degrees')
    degree = models.CharField(max_length=255)

    panels = [FieldPanel('degree')]

class StudentPageExhibition(Orderable):
    page = ParentalKey('rca.StudentPage', related_name='exhibitions')
    exhibition = models.CharField(max_length=255, blank=True)

    panels = [FieldPanel('exhibition')]

class StudentPageExperience(Orderable):
    page = ParentalKey('rca.StudentPage', related_name='experiences')
    experience = models.CharField(max_length=255, blank=True)

    panels = [FieldPanel('experience')]

class StudentPageAwards(Orderable):
    page = ParentalKey('rca.StudentPage', related_name='awards')
    award = models.CharField(max_length=255, blank=True)

    panels = [FieldPanel('award')]

class StudentPageContactsEmail(Orderable):
    page = ParentalKey('rca.StudentPage', related_name='email')
    email = models.EmailField(max_length=255, blank=True)

    panels = [FieldPanel('email')]

class StudentPageContactsPhone(Orderable):
    page = ParentalKey('rca.StudentPage', related_name='phone')
    phone = models.CharField(max_length=255, blank=True)

    panels = [FieldPanel('phone')]

class StudentPageContactsWebsite(Orderable):
    page = ParentalKey('rca.StudentPage', related_name='website')
    website = models.URLField(max_length=255, blank=True)

    panels = [FieldPanel('website')]

class StudentPageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.StudentPage', related_name='carousel_items')

class StudentPageWorkCollaborator(Orderable):
    page = ParentalKey('rca.StudentPage', related_name='collaborators')
    name = models.CharField(max_length=255, blank=True)

    panels = [FieldPanel('name')]

class StudentPageWorkSponsor(Orderable):
    page = ParentalKey('rca.StudentPage', related_name='sponsor')
    name = models.CharField(max_length=255, blank=True)

    panels = [FieldPanel('name')]

class StudentPage(Page, SocialFields):
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES)
    programme = models.CharField(max_length=255, choices=ALL_PROGRAMMES)
    degree_qualification = models.CharField(max_length=255, choices=QUALIFICATION_CHOICES)
    degree_subject = models.CharField(max_length=255, choices=SUBJECT_CHOICES)
    degree_year = models.CharField(max_length=4)
    specialism = models.CharField(max_length=255, blank=True)
    profile_image = models.ForeignKey('rca.RcaImage', on_delete=models.SET_NULL, related_name='+', null=True, blank=True)
    statement = RichTextField(blank=True)
    work_description = RichTextField(blank=True)
    work_type = models.CharField(max_length=255, choices=WORK_TYPES_CHOICES, blank=True)
    work_location = models.CharField(max_length=255, choices=CAMPUS_CHOICES, blank=True)
    work_awards = models.CharField(max_length=255, blank=True)
    funding = models.CharField(max_length=255, blank=True)
    student_twitter_feed = models.CharField(max_length=255, blank=True, help_text="Enter Twitter handle without @ symbol.")
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=TWITTER_FEED_HELP_TEXT)
    rca_content_id = models.CharField(max_length=255, blank=True)  # for import
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    supervisor = models.ForeignKey('rca.StaffPage', on_delete=models.SET_NULL, related_name='+', null=True, blank=True)
    show_on_homepage = models.BooleanField()

    indexed_fields = ('get_school_display', 'get_programme_display', 'statement')

    search_name = 'Student'

StudentPage.content_panels = [
    FieldPanel('title', classname="full title"),
    MultiFieldPanel([
        FieldPanel('first_name'),
        FieldPanel('last_name'),
    ], 'Full name'),
    FieldPanel('school'),
    FieldPanel('programme'),
    FieldPanel('specialism'),
    FieldPanel('degree_qualification'),
    FieldPanel('degree_subject'),
    FieldPanel('degree_year'),
    PageChooserPanel('supervisor'),
    ImageChooserPanel('profile_image'),
    InlinePanel(StudentPage, 'email', label="Email"),
    InlinePanel(StudentPage, 'phone', label="Phone"),
    InlinePanel(StudentPage, 'website', label="Website"),
    FieldPanel('student_twitter_feed'),
    InlinePanel(StudentPage, 'degrees', label="Previous degrees"),
    InlinePanel(StudentPage, 'exhibitions', label="Exhibition"),
    InlinePanel(StudentPage, 'experiences', label="Experience"),
    InlinePanel(StudentPage, 'awards', label="Awards"),
    FieldPanel('statement', classname="full"),
    InlinePanel(StudentPage, 'carousel_items', label="Carousel content"),
    FieldPanel('work_description', classname="full"),
    FieldPanel('work_type'),
    FieldPanel('work_location'),
    FieldPanel('funding'),
    InlinePanel(StudentPage, 'collaborators', label="Work collaborator"),
    InlinePanel(StudentPage, 'sponsor', label="Work sponsor"),
    FieldPanel('work_awards'),
    FieldPanel('twitter_feed'),
]

StudentPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('show_on_homepage'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]

# == RCA Now page ==

class RcaNowPagePageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.RcaNowPage', related_name='carousel_items')


class RcaNowPageTag(TaggedItemBase):
    content_object = ParentalKey('rca.RcaNowPage', related_name='tagged_items')


class RcaNowPage(Page, SocialFields):
    body = RichTextField()
    author = models.CharField(max_length=255, blank=True)
    date = models.DateField("Creation date")
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES)
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES)
    area = models.CharField(max_length=255, choices=AREA_CHOICES, blank=True)
    show_on_homepage = models.BooleanField()
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=TWITTER_FEED_HELP_TEXT)

    tags = ClusterTaggableManager(through=RcaNowPageTag)

    indexed_fields = ('body', 'author', 'get_programme_display', 'get_school_display', 'get_area_display')

    search_name = 'RCA Now'

RcaNowPage.content_panels = [
    InlinePanel(RcaNowPage, 'carousel_items', label="Carousel content"),
    FieldPanel('title', classname="full title"),
    FieldPanel('body', classname="full"),
    FieldPanel('author'),
    FieldPanel('date'),
    FieldPanel('school'),
    FieldPanel('programme'),
    FieldPanel('area'),
    FieldPanel('twitter_feed'),
]

RcaNowPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('show_on_homepage'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
    # InlinePanel(RcaNowPage, 'tagged_items', label='tag'),
    FieldPanel('tags'),
]


# == RCA Now index ==


class RcaNowIndex(Page, SocialFields):
    intro = RichTextField(blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=TWITTER_FEED_HELP_TEXT)

    indexed = False

    def serve(self, request):
        programme = request.GET.get('programme')
        school = request.GET.get('school')
        area = request.GET.get('area')

        rca_now_items = RcaNowPage.objects.filter(live=True)

        if programme:
            rca_now_items = rca_now_items.filter(programme=programme)
        if school:
            rca_now_items = rca_now_items.filter(school=school)
        if area:
            rca_now_items = rca_now_items.filter(area=area)

        related_programmes = SCHOOL_PROGRAMME_MAP[school] if school else []

        rca_now_items = rca_now_items.order_by('-date')

        page = request.GET.get('page')
        paginator = Paginator(rca_now_items, 10)  # Show 10 rca now items per page
        try:
            rca_now_items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            rca_now_items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            rca_now_items = paginator.page(paginator.num_pages)

        if request.is_ajax():
            return render(request, "rca/includes/rca_now_listing.html", {
                'self': self,
                'rca_now_items': rca_now_items,
                'related_programmes': related_programmes,
            })
        else:
            return render(request, self.template, {
                'self': self,
                'rca_now_items': rca_now_items
            })

RcaNowIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    FieldPanel('twitter_feed'),
]

RcaNowIndex.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]

# == Research Item page ==

class ResearchItemCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.ResearchItem', related_name='carousel_items')

class ResearchItemCreator(Orderable):
    page = ParentalKey('rca.ResearchItem', related_name='creator')
    person = models.ForeignKey('core.Page', null=True, blank=True, related_name='+', help_text="Choose an existing person's page, or enter a name manually below (which will not be linked).")
    manual_person_name= models.CharField(max_length=255, blank=True, help_text="Only required if the creator has no page of their own to link to")

    panels=[
        PageChooserPanel('person'),
        FieldPanel('manual_person_name')
    ]

class ResearchItemLink(Orderable):
    page = ParentalKey('rca.ResearchItem', related_name='links')
    link = models.URLField()
    link_text = models.CharField(max_length=255)

    panels=[
        FieldPanel('link'),
        FieldPanel('link_text')
    ]
class ResearchItem(Page, SocialFields):
    research_type = models.CharField(max_length=255, choices=RESEARCH_TYPES_CHOICES)
    ref = models.BooleanField(default=False, blank=True)
    year = models.CharField(max_length=4)
    description = RichTextField()
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES)
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True)
    work_type = models.CharField(max_length=255, choices=WORK_TYPES_CHOICES)
    work_type_other = models.CharField("'Other' work type", max_length=255, blank=True)
    theme = models.CharField(max_length=255, choices=WORK_THEME_CHOICES)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=TWITTER_FEED_HELP_TEXT)
    rca_content_id = models.CharField(max_length=255, blank=True) # for import
    eprintid = models.CharField(max_length=255, blank=True) # for import
    show_on_homepage = models.BooleanField()

    indexed_fields = ('get_research_type_display', 'description', 'get_school_display', 'get_programme_display', 'get_work_type_display', 'work_type_other', 'get_theme_display')

    search_name = 'Research'

    def get_related_news(self, count=4):
        return NewsItem.get_related(
            area='research',
            programmes=([self.programme] if self.programme else None),
            schools=([self.school] if self.school else None),
            count=count,
        )

ResearchItem.content_panels = [
    FieldPanel('title', classname="full title"),
    InlinePanel(ResearchItem, 'carousel_items', label="Carousel content"),
    FieldPanel('research_type'),
    InlinePanel(ResearchItem, 'creator', label="Creator"),
    FieldPanel('ref'),
    FieldPanel('year'),
    FieldPanel('school'),
    FieldPanel('programme'),
    FieldPanel('work_type'),
    FieldPanel('work_type_other'),
    FieldPanel('theme'),
    FieldPanel('description'),
    InlinePanel(ResearchItem, 'links', label="Links"),
    FieldPanel('twitter_feed'),
]

ResearchItem.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('show_on_homepage'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]


# == Research Innovation page ==


class ResearchInnovationPageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.ResearchInnovationPage', related_name='carousel_items')

class ResearchInnovationPageTeaser(Orderable):
    page = ParentalKey('rca.ResearchInnovationPage', related_name='teasers')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    url = models.URLField(blank=True)
    title = models.CharField(max_length=255, blank=True)
    text = models.CharField(max_length=255, blank=True)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('url'),
        FieldPanel('title', classname="full title"),
        FieldPanel('text'),
    ]

class ResearchInnovationPageRelatedLink(Orderable):
    page = ParentalKey('rca.ResearchInnovationPage', related_name='related_links')
    link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    link_text = models.CharField(max_length=255, help_text="Alternative link title (default is target page's title)")

    panels = [
        PageChooserPanel('link'),
        FieldPanel('link_text'),
    ]

class ResearchInnovationPageContactPhone(Orderable):
    page = ParentalKey('rca.ResearchInnovationPage', related_name='contact_phone')
    phone_number = models.CharField(max_length=255)

    panels = [
        FieldPanel('phone_number')
    ]

class ResearchInnovationPageContactEmail(Orderable):
    page = ParentalKey('rca.ResearchInnovationPage', related_name='contact_email')
    email_address = models.CharField(max_length=255)

    panels = [
        FieldPanel('email_address')
    ]

class ResearchInnovationPageCurrentResearch(Orderable):
    page = ParentalKey('rca.ResearchInnovationPage', related_name='current_research')
    link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')

    panels = [
        PageChooserPanel('link'),
    ]

    class Meta:
        # needs to be shortened to avoid hitting limit on the permissions table - https://code.djangoproject.com/ticket/8548
        verbose_name = "research innov. page current research"

class ResearchInnovationPageAd(Orderable):
    page = ParentalKey('rca.ResearchInnovationPage', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+')

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class ResearchInnovationPage(Page, SocialFields):
    intro = RichTextField(blank=True)
    intro_link = models.ForeignKey('core.Page', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    teasers_title = models.CharField(max_length=255, blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=TWITTER_FEED_HELP_TEXT)
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text="The full bleed image in the background")
    contact_title = models.CharField(max_length=255, blank=True)
    contact_address = models.TextField(blank=True)
    contact_link = models.URLField(blank=True)
    contact_link_text = models.CharField(max_length=255, blank=True)
    news_carousel_area = models.CharField(max_length=255, choices=AREA_CHOICES, blank=True)

    indexed = False

ResearchInnovationPage.content_panels = [
    FieldPanel('title', classname="full title"),
    MultiFieldPanel([
        FieldPanel('intro', classname="full"),
        PageChooserPanel('intro_link'),
    ],'Introduction'),
    InlinePanel(ResearchInnovationPage, 'current_research', label="Current research"),
    InlinePanel(ResearchInnovationPage, 'carousel_items', label="Carousel content"),
    FieldPanel('teasers_title'),
    InlinePanel(ResearchInnovationPage, 'teasers', label="Teaser content"),
    InlinePanel(ResearchInnovationPage, 'related_links', label="Related links"),
    InlinePanel(ResearchInnovationPage, 'manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
    ImageChooserPanel('background_image'),
    MultiFieldPanel([
        FieldPanel('contact_title'),
        FieldPanel('contact_address'),
        FieldPanel('contact_link'),
        FieldPanel('contact_link_text'),

    ],'Contact'),
    InlinePanel(ResearchInnovationPage, 'contact_phone', label="Contact phone number"),
    InlinePanel(ResearchInnovationPage, 'contact_email', label="Contact email address"),
    FieldPanel('news_carousel_area'),
]

ResearchInnovationPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]


# == Current research page ==
class CurrentResearchPageAd(Orderable):
    page = ParentalKey('rca.CurrentResearchPage', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+')

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class CurrentResearchPage(Page, SocialFields):
    intro = RichTextField(blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=TWITTER_FEED_HELP_TEXT)

    indexed = False

    def serve(self, request):
        research_type = request.GET.get('research_type')
        school = request.GET.get('school')
        theme = request.GET.get('theme')
        work_type = request.GET.get('work_type')

        research_items = ResearchItem.objects.filter(live=True).order_by('?')

        if research_type:
            research_items = research_items.filter(research_type=research_type)
        if school:
            research_items = research_items.filter(school=school)
        if theme:
            research_items = research_items.filter(theme=theme)
        if work_type:
            research_items = research_items.filter(work_type=work_type)

        research_items.order_by('-year')

        page = request.GET.get('page')
        paginator = Paginator(research_items, 8)  # Show 8 research items per page
        try:
            research_items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            research_items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            research_items = paginator.page(paginator.num_pages)

        if request.is_ajax():
            return render(request, "rca/includes/current_research_listing.html", {
                'self': self,
                'research_items': research_items
            })
        else:
            return render(request, self.template, {
                'self': self,
                'research_items': research_items
            })

CurrentResearchPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel(CurrentResearchPage, 'manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
]

CurrentResearchPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]

# == Gallery Page ==

class GalleryPageRelatedLink(Orderable):
    page = ParentalKey('rca.GalleryPage', related_name='related_links')
    link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    link_text = models.CharField(max_length=255, help_text="Alternative link title (default is target page's title)")

    panels = [
        PageChooserPanel('link'),
        FieldPanel('link_text'),
    ]

class GalleryPage(Page, SocialFields):
    intro = RichTextField(blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=TWITTER_FEED_HELP_TEXT)

    def serve(self, request):
        programme = request.GET.get('programme')
        school = request.GET.get('school')
        year = request.GET.get('degree_year')

        gallery_items = StudentPage.objects.filter(live=True).exclude(degree_qualification="researchstudent").order_by('?')
        if programme:
            gallery_items = gallery_items.filter(programme=programme)
        if school:
            gallery_items = gallery_items.filter(school=school)
        if year:
            gallery_items = gallery_items.filter(degree_year=year)

        gallery_items = gallery_items.order_by('?');

        related_programmes = SCHOOL_PROGRAMME_MAP[school] if school else []


        page = request.GET.get('page')
        paginator = Paginator(gallery_items, 5)  # Show 5 gallery items per page
        try:
            gallery_items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            gallery_items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            gallery_items = paginator.page(paginator.num_pages)

        if request.is_ajax():
            return render(request, "rca/includes/gallery_listing.html", {
                'self': self,
                'gallery_items': gallery_items,
                'related_programmes': related_programmes,
            })
        else:
            return render(request, self.template, {
                'self': self,
                'gallery_items': gallery_items
            })

GalleryPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    FieldPanel('twitter_feed'),
    InlinePanel(GalleryPage, "related_links", label="Related links")
]

GalleryPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]

# == Contact Us page ==

class ContactUsPage(Page, SocialFields):
    pass

ContactUsPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]


# == Donation page ==


class DonationPage(Page, SocialFields):
    redirect_to_when_done = models.ForeignKey('core.Page', null=True, blank=False, on_delete=models.PROTECT, related_name='+')
    payment_description = models.CharField(max_length=255, blank=True, help_text="This value will be stored along with each donation made on this page to help ditinguish them from donations on other pages.")

    # fields copied from StandrdPage
    intro = RichTextField(blank=True)
    body = RichTextField(blank=True)
    strapline = models.CharField(max_length=255, blank=True)
    middle_column_body = RichTextField(blank=True)
    show_on_homepage = models.BooleanField()

    indexed_fields = ('intro', 'body')

    search_name = None

    def serve(self, request):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        if request.method == "GET":
            form = DonationForm()
        if request.method == "POST":
            form = DonationForm(request.POST)
            if form.is_valid():
                try:
                    # When exporting the payments from the dashboard
                    # the metadata field is not exported but the description is,
                    # so we duplicate the metadata there as well.
                    charge = stripe.Charge.create(
                        card=form.cleaned_data.get('stripe_token'),
                        amount=form.cleaned_data.get('amount'),  # amount in cents (converted by the form)
                        currency="gbp",
                        description=self.payment_description,
                        metadata=form.cleaned_data.get('metadata', {}),
                    )
                    return HttpResponseRedirect(self.redirect_to_when_done.url)
                except stripe.CardError, e:
                    # CardErrors are displayed to the user
                    messages.error(request, e['message'])
                except Exception, e:
                    # for other exceptions we send emails to admins and display a user freindly error message
                    # InvalidRequestError (if token is used more than once), APIError (server is not reachable), AuthenticationError
                    mail_exception(e, prefix=" [stripe] ")
                    logging.error("[stripe] ", exc_info=full_exc_info())
                    messages.error(request, "There was a problem processing your payment. Please try again later.")

        return render(request, self.template, {
            'self': self,
            'form': form,
            'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY,
        })

DonationPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('strapline', classname="full"),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    FieldPanel('middle_column_body', classname="full"),
    MultiFieldPanel([
        FieldPanel('payment_description', classname="full"),
        PageChooserPanel('redirect_to_when_done'),
    ], "Donation details")
    # InlinePanel(DonationPage, 'carousel_items', label="Carousel content"),
    # InlinePanel(DonationPage, 'related_links', label="Related links"),
    # InlinePanel(DonationPage, 'reusable_text_snippets', label="Reusable text snippet"),
    # InlinePanel(DonationPage, 'documents', label="Document"),
    # InlinePanel(DonationPage, 'quotations', label="Quotation"),
    # InlinePanel(DonationPage, 'images', label="Middle column image"),
    # InlinePanel(DonationPage, 'manual_adverts', label="Manual adverts"),
]

DonationPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('show_on_homepage'),
        ImageChooserPanel('feed_image'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]
