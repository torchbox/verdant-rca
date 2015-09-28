from datetime import date
import datetime
import logging
import random

from itertools import chain

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.signals import user_logged_in
from django.db import models
from django.db.models import Min, Max
from django.db.models.signals import pre_delete

from django.dispatch.dispatcher import receiver
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.views.decorators.vary import vary_on_headers

from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailcore.url_routing import RouteResult
from modelcluster.fields import ParentalKey

from wagtail.wagtailadmin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel, PageChooserPanel, PublishingPanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailimages.models import Image, AbstractImage, AbstractRendition
from wagtail.wagtaildocs.edit_handlers import DocumentChooserPanel
from wagtail.wagtailsnippets.edit_handlers import SnippetChooserPanel
from wagtail.wagtailsnippets.models import register_snippet
from wagtail.wagtailsearch import index

from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase, Tag

from donations.forms import DonationForm
from donations.mail_admins import mail_exception, full_exc_info
import stripe

import hashlib

from rca.filters import run_filters, run_filters_q, combine_filters, get_filters_q
import json

from rca_signage.constants import SCREEN_CHOICES
from reachout_choices import REACHOUT_PROJECT_CHOICES, REACHOUT_PARTICIPANTS_CHOICES, REACHOUT_THEMES_CHOICES, REACHOUT_PARTNERSHIPS_CHOICES

from .help_text import help_text


# RCA defines its own custom image class to replace wagtailimages.Image,
# providing various additional data fields
class RcaImage(AbstractImage):
    alt = models.CharField(max_length=255, blank=True, help_text=help_text('rca.RcaImage', 'alt'))
    creator = models.CharField(max_length=255, blank=True, help_text=help_text('rca.RcaImage', 'creator'))
    year = models.CharField(max_length=255, blank=True, help_text=help_text('rca.RcaImage', 'year'))
    medium = models.CharField(max_length=255, blank=True, help_text=help_text('rca.RcaImage', 'medium'))
    dimensions = models.CharField(max_length=255, blank=True, help_text=help_text('rca.RcaImage', 'dimensions'))
    permission = models.CharField(max_length=255, blank=True, help_text=help_text('rca.RcaImage', 'permission'))
    photographer = models.CharField(max_length=255, blank=True, help_text=help_text('rca.RcaImage', 'photographer'))
    rca_content_id = models.CharField(max_length=255, blank=True, editable=False) # for import
    eprint_docid = models.CharField(max_length=255, blank=True, editable=False) # for import

    admin_form_fields = Image.admin_form_fields + (
        'alt', 'creator', 'year', 'medium', 'dimensions', 'permission', 'photographer'
    )

    search_fields = AbstractImage.search_fields + (
        index.SearchField('creator'),
        index.SearchField('photographer'),
    )

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
            ('image', 'filter', 'focal_point_key'),
        )

# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(pre_delete, sender=RcaRendition)
def rendition_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)


AREA_CHOICES = (
    ('administration', 'Administration'),
    ('alumnirca', 'AlumniRCA'),
    ('communicationsmarketing', 'Communications & Marketing'),
    ('development', 'Development'),
    ('drawingstudio', 'Drawing Studio'),
    ('executiveeducation', 'Executive Education'),
    ('fuelrca', 'Fuel RCA'),
    ('helenhamlyn', 'The Helen Hamlyn Centre for Design'),
    ('informationlearningtechnicalservices', 'Information, Learning & Technical Services'),
    ('innovationrca', 'InnovationRCA'),
    ('reachoutrca', 'ReachOutRCA'),
    ('research-knowledgeexchange', "Research, Knowledge Exchange & Innovation"),
    ('schoolofarchitecture', 'School of Architecture'),
    ('schoolofcommunication', 'School of Communication'),
    ('schoolofdesign', 'School of Design'),
    ('schooloffineart', 'School of Fine Art'),
    ('schoolofhumanities', 'School of Humanities'),
    ('schoolofmaterial', 'School of Material'),
    ('showrca', 'Show RCA'),
    ('support', 'Support'),
    ('sustainrca', 'SustainRCA'),
)

STAFF_AREA_CHOICES = AREA_CHOICES + (
    ('performance', "Performance"),
    ('moving-image', "Moving image"),
)

EVENT_AREA_CHOICES = AREA_CHOICES + (
    ('alumnirca', 'AlumniRCA'),
)

EVENT_AUDIENCE_CHOICES = (
    ('public', 'Public'),
    ('rcaonly', 'RCA only'),
    ('openday', 'Open Day'),
    ('rcatalks', 'RCA talks'),
    ('rcaalumnionly', 'RCA Alumni Only'),
)

EVENT_LOCATION_CHOICES = (
    ('kensington', 'Kensington'),
    ('battersea', 'Battersea'),
    ('collegewide', 'College-wide'),
    ('other', 'Other/External (enter below)')
)

CAMPUS_CHOICES = (
    ('kensington', 'Kensington'),
    ('battersea', 'Battersea'),
)

EVENT_GALLERY_CHOICES = (
    ('courtyardgalleries', 'Courtyard Galleries'),
    ('cwadseminarroom', 'Critical Writing in Art & Design Seminar Room'),
    ('ccaseminarroom', 'Curating Contemporary Art Seminar Room'),
    ('danacentre', 'Dana Centre'),
    ('drawingstudio', 'Drawing Studio'),
    ('dysonbuilding', 'Dyson Building'),
    ('gorvylecturetheatre', 'Gorvy Lecture Theatre'),
    ('henrymooregallery', 'Henry Moore Gallery'),
    ('humanitiesseminarroom', 'Humanities Seminar Room'),
    ('jaymewsgallery', 'Jay Mews Gallery'),
    ('lecturetheatre1', 'Lecture Theatre 1'),
    ('lecturetheatre2', 'Lecture Theatre 2'),
    ('library', 'Library'),
    ('linkgallery', 'Link Gallery'),
    ('lowergulbenkiangallery', 'Lower Gulbenkian Gallery'),
    ('movingimagestudio', 'Moving Image Studio'),
    ('palstevensbuilding', 'PAL, Stevens Building'),
    ('photographystudios', 'Photography Studios'),
    ('printmakingstudios', 'Printmaking Studios'),
    ('sacklerbuilding', 'Sackler Building'),
    ('senior-common-room', 'Senior Common Room'),
    ('sculpturebuilding', 'Sculpture Building'),
    ('studiorca', 'StudioRCA'),
    ('testbed1', 'Testbed 1'),
    ('uppergulbenkiangallery', 'Upper Gulbenkian Gallery'),
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
    ('mphil_by_thesis', 'MPhil by Thesis'),
    ('phd_by_thesis', 'PhD by Thesis'),
    ('mphil_by_practice', 'MPhil by Practice'),
    ('phd_by_practice', 'PhD by Practice'),
    ('other', 'Other (enter below)'),
)

SHOW_WORK_TYPE_CHOICES = (
    ('dissertation', "Dissertation"),
    ('major-project', "Major project")
)

WORK_THEME_CHOICES = (
    ('culturesofcurating', 'Cultures of Curating'),
    ('designinnovationandsociety', 'Design, Innovation and Society'),
    ('dialoguesofformandsurface', 'Dialogues of Form and Surface'),
    ('imageandlanguage', 'Image and Language')
)

INNOVATIONRCA_PROJECT_TYPES_CHOICES = (
    ('startup', 'Start-up'),
    ('fellowship', 'Fellowship'),
)

SPECIALISM_CHOICES = (
    ('ads1', 'ADS1'),
    ('ads2', 'ADS2'),
    ('ads3', 'ADS3'),
    ('ads4', 'ADS4'),
    ('ads5', 'ADS5'),
    ('ads6', 'ADS6'),
    ('ads7', 'ADS7'),
    ('ads9', 'ADS9'),
    ('knit', 'Knit'),
    ('mixed media', 'Mixed media'),
    ('print', 'Print'),
    ('weave', 'Weave'),
    ('performance', 'Performance'),
    ('movingimage', 'Moving Image'),
    ('platform13', 'Platform 13'),
    ('platform14', 'Platform 14'),
    ('platform15', 'Platform 15'),
    ('platform17', 'Platform 17'),
    ('platform18', 'Platform 18'),
    ('platform21', 'Platform 21'),
    ('footwear-accessories-millinery', "Footwear, Accessories & Millinery"),
)

SCHOOL_CHOICES = (
    ('schoolofarchitecture', 'School of Architecture'),
    ('schoolofcommunication', 'School of Communication'),
    ('schoolofdesign', 'School of Design'),
    ('schooloffineart', 'School of Fine Art'),
    ('schoolofhumanities', 'School of Humanities'),
    ('schoolofmaterial', 'School of Material'),
    ('helenhamlyn', 'The Helen Hamlyn Centre for Design'),
    ('rectorate', 'Rectorate'),
    ('innovationrca', 'InnovationRCA'),
)

ALL_PROGRAMMES = tuple(sorted([
    ('fashionwomenswear', 'Fashion Womenswear'),
    ('textiles', 'Textiles'),
    ('ceramicsglass', 'Ceramics & Glass'),
    ('sculpture', 'Sculpture'),
    ('designproducts', 'Design Products'),
    ('industrialdesignengineering', 'Industrial Design Engineering'),
    ('goldsmithingsilversmithingmetalworkjewellery', 'Goldsmithing, Silversmithing, Metalwork & Jewellery'),
    ('jewelleryandmetal', 'Jewellery & Metal'),
    ('visualcommunication', 'Visual Communication'),
    ('designinteractions', 'Design Interactions'),
    ('innovationdesignengineering', 'Innovation Design Engineering'),
    ('historyofdesign', 'History of Design'),
    ('fashionmenswear', 'Fashion Menswear'),
    ('printmaking', 'Printmaking'),
    ('globalinnovationdesign', 'Global Innovation Design'),
    ('architecture', 'Architecture'),
    ('interiordesign', 'Interior Design'),
    ('drawingstudio', 'Drawing Studio'),
    ('criticalhistoricalstudies', 'Critical & Historical Studies'),
    ('painting', 'Painting'),
    ('photography', 'Photography'),
    ('servicedesign', 'Service Design'),
    ('animation', 'Animation'),
    ('informationexperiencedesign', 'Information Experience Design'),
    ('criticalwritinginartdesign', 'Critical Writing in Art & Design'),
    ('curatingcontemporaryart', 'Curating Contemporary Art'),
    ('conservation', 'Conservation'),
    ('vehicledesign', 'Vehicle Design'),
    ('communicationartdesign', 'Communication Art & Design'),
], key=lambda programme: programme[0])) # ALL_PROGRAMMES needs to be in alphabetical order (#504 Issue 1)


SCHOOL_PROGRAMME_MAP = {
    '2015': {
        'schoolofarchitecture': ['architecture', 'interiordesign'],
        'schoolofcommunication': ['animation', 'informationexperiencedesign', 'visualcommunication'],
        'schoolofdesign': ['designinteractions', 'designproducts', 'globalinnovationdesign', 'innovationdesignengineering', 'servicedesign', 'vehicledesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['criticalhistoricalstudies', 'criticalwritinginartdesign', 'curatingcontemporaryart', 'historyofdesign'],
        'schoolofmaterial': ['ceramicsglass', 'jewelleryandmetal', 'fashionmenswear', 'fashionwomenswear', 'textiles'],
    },
    '2014': {
        'schoolofarchitecture': ['architecture', 'interiordesign'],
        'schoolofcommunication': ['animation', 'informationexperiencedesign', 'visualcommunication'],
        'schoolofdesign': ['designinteractions', 'designproducts', 'globalinnovationdesign', 'innovationdesignengineering', 'servicedesign', 'vehicledesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['criticalhistoricalstudies', 'criticalwritinginartdesign', 'curatingcontemporaryart', 'historyofdesign'],
        'schoolofmaterial': ['ceramicsglass', 'goldsmithingsilversmithingmetalworkjewellery', 'jewelleryandmetal', 'fashionmenswear', 'fashionwomenswear', 'textiles'],
    },
    '2013': {
        'schoolofarchitecture': ['architecture'],
        'schoolofcommunication': ['animation', 'visualcommunication'],
        'schoolofdesign': ['designinteractions', 'designproducts', 'innovationdesignengineering', 'servicedesign', 'vehicledesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['criticalhistoricalstudies', 'criticalwritinginartdesign', 'curatingcontemporaryart', 'historyofdesign'],
        'schoolofmaterial': ['ceramicsglass', 'goldsmithingsilversmithingmetalworkjewellery', 'fashionmenswear', 'fashionwomenswear', 'textiles'],
    },
    '2012': {
        'schoolofarchitecture': ['architecture'],
        'schoolofcommunication': ['animation', 'visualcommunication'],
        'schoolofdesign': ['designinteractions', 'designproducts', 'innovationdesignengineering', 'vehicledesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['criticalhistoricalstudies', 'criticalwritinginartdesign', 'curatingcontemporaryart', 'historyofdesign'],
        'schoolofmaterial': ['ceramicsglass', 'goldsmithingsilversmithingmetalworkjewellery', 'fashionmenswear', 'fashionwomenswear', 'textiles'],
    },
    '2011': {
        'schoolofarchitecture': ['architecture'],
        'schoolofcommunication': ['animation', 'communicationartdesign'],
        'schoolofdesign': ['designinteractions', 'designproducts', 'innovationdesignengineering', 'vehicledesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['criticalhistoricalstudies', 'criticalwritinginartdesign', 'curatingcontemporaryart', 'historyofdesign'],
        'schoolofmaterial': ['ceramicsglass', 'goldsmithingsilversmithingmetalworkjewellery', 'fashionmenswear', 'fashionwomenswear', 'textiles'],
    },
    '2010': {
        'schoolofarchitecture': ['architecture'],
        'schoolofcommunication': ['animation', 'communicationartdesign'],
        'schoolofdesign': ['designinteractions', 'designproducts', 'innovationdesignengineering', 'vehicledesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['criticalhistoricalstudies', 'criticalwritinginartdesign', 'curatingcontemporaryart', 'historyofdesign'],
        'schoolofmaterial': ['ceramicsglass', 'goldsmithingsilversmithingmetalworkjewellery', 'fashionmenswear', 'fashionwomenswear', 'textiles'],
    },
    '2009': {
        'schoolofcommunication': ['animation', 'communicationartdesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['conservation', 'criticalhistoricalstudies', 'curatingcontemporaryart', 'historyofdesign'],
    },
    '2008': {
        'schoolofcommunication': ['animation', 'communicationartdesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['conservation', 'criticalhistoricalstudies', 'curatingcontemporaryart', 'historyofdesign'],
    },
    '2007': {
        'schoolofcommunication': ['animation', 'communicationartdesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['conservation', 'criticalhistoricalstudies', 'curatingcontemporaryart', 'historyofdesign'],
    },
}

SUSTAINRCA_CATEGORY_CHOICES = (
    ('solutionsforsociety', 'Solutions for Society'),
    ('inspiredproducts', 'Inspired Products'),
    ('visionaryprocess', 'Visionary Process'),
    ('movingminds', 'Moving Minds')
)

# generate choices for programmes groupped by year, based on SCHOOL_PROGRAMME_MAP
PROGRAMME_CHOICES = sorted([
    (
        year,   tuple([
                    (programme, dict(ALL_PROGRAMMES)[programme])
                    for programme
                    in sorted(set(sum(mapping.values(), [])))
                ])
    )
    for year, mapping
    in SCHOOL_PROGRAMME_MAP.items()
], reverse=True)


def get_programme_synonyms(programme):
    """ Find all programme identifiers that appear on the same programme page.
        E.g. jewelleryandmetal and goldsmithingsilversmithingmetalworkjewellery
        are both associated with the same ProgrammePage and if one of them
        is selected in a filter then we want to return results for both.
    """
    programmes = ProgrammePageProgramme.objects\
        .filter(page__programmes__programme=programme)\
        .only('programme')\
        .distinct()\
        .values_list('programme', flat=True)

    if programmes.exists():
        return list(programmes)
    else:
        return [programme]


# Make sure the values in SCHOOL_PROGRAMME_MAP are valid (`sum(list, [])` flattens a list)
# 1. check schools
assert set(sum([mapping.keys() for mapping in SCHOOL_PROGRAMME_MAP.values()], []))\
        .issubset(set(dict(SCHOOL_CHOICES)))
# 2. check programmes
assert set(sum([sum(mapping.values(), []) for mapping in SCHOOL_PROGRAMME_MAP.values()], []))\
        .issubset(set(dict(ALL_PROGRAMMES)))

YEARS = list(sorted(SCHOOL_PROGRAMME_MAP.keys()))

SCHOOL_CHOICES_MAP = dict(SCHOOL_CHOICES)

# A list of all schools that are mentioned in SCHOOL_PROGRAMME_MAP
SHOW_SCHOOLS = tuple(
    (school_slug, SCHOOL_CHOICES_MAP[school_slug])
    for school_slug in {
        school for school in mapping
        for year, mapping
        in SCHOOL_PROGRAMME_MAP.items()
    }
)

SUBJECT_CHOICES = ALL_PROGRAMMES + (
    ('curatingcontemporaryartcollegebased', 'Curating Contemporary Art (College-based)'),
    ('curatingcontemporaryartworkbased', 'Curating Contemporary Art (Work-based)'),
)

QUALIFICATION_CHOICES = (
    ('ma', 'MA'),
    ('mphil', 'MPhil'),
    ('phd', 'PhD'),
    ('researchstudent', 'Research Student'),
    ('innovationrca-fellow', 'InnovationRCA Fellow'),
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

STAFF_LOCATION_CHOICES = (
    ('ceramicsgsmj', 'Ceramics, Glass, Metalwork & Jewellery'),
    ('darwinworshops', 'Darwin Workshops'),
    ('fashiontextiles', 'Fashion & Textiles'),
    ('lensbasedmediaaudio', 'Lens-based Media and Audio'),
    ('paintingsculpture', 'Painting & Sculpture'),
    ('printmakingletterpress', 'Printmaking & Letterpress'),
    ('rapidform', 'Rapidform'),
)

STATUS_CHOICES = (
    ('fulltime', 'Full time'),
    ('parttime', 'Part time'),
)

DEGREE_TYPE_CHOICES = (
    ('practicebased', 'Practice based'),
    ('thesisonly', 'Thesis only'),
)

TWITTER_FEED_HELP_TEXT = "Replace the default Twitter feed by providing an alternative Twitter handle (without the @ symbol)"
# Generic fields to opt out of events and twitter blocks
class OptionalBlockFields(models.Model):
    exclude_twitter_block = models.BooleanField(default=False, help_text=help_text('rca.OptionalBlockFields', 'exclude_twitter_block'))
    exclude_events_sidebar = models.BooleanField(default=False, help_text=help_text('rca.OptionalBlockFields', 'exclude_events_sidebar'))
    exclude_global_adverts = models.BooleanField(default=False, help_text=help_text('rca.OptionalBlockFields', 'exclude_global_adverts'))

    class Meta:
        abstract = True

# Generic social fields abstract class to add social image/text to any new content type easily.
class SocialFields(models.Model):
    social_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.SocialFields', 'social_image'))
    social_text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.SocialFields', 'social_text'))

    class Meta:
        abstract = True

# Fields that configure how the sidebar of a given page should be treated
class SidebarBehaviourFields(models.Model):
    collapse_upcoming_events = models.BooleanField(default=False, help_text=help_text('rca.SidebarBehaviourFields', 'collapse_upcoming_events'))

    class Meta:
        abstract = True


# Carousel item abstract class - all carousels basically require the same fields
class CarouselItemFields(models.Model):
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.CarouselItemFields', 'image'))
    overlay_text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.CarouselItemFields', 'overlay_text'))
    link = models.URLField("External link", blank=True, help_text=help_text('rca.CarouselItemFields', 'link'))
    link_page = models.ForeignKey(Page, on_delete=models.SET_NULL, related_name='+', null=True, blank=True, help_text=help_text('rca.CarouselItemFields', 'link_page'))
    embedly_url = models.URLField('Vimeo URL', blank=True, help_text=help_text('rca.CarouselItemFields', 'embedly_url'))
    poster_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.CarouselItemFields', 'poster_image'))

    @property
    def get_link(self):
        if self.link_page:
            return self.link_page.url
        else:
            return self.link

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('overlay_text'),
        FieldPanel('link'),
        PageChooserPanel('link_page'),
        FieldPanel('embedly_url'),
        ImageChooserPanel('poster_image'),
    ]

    class Meta:
        abstract = True

# Related link item abstract class - all related links basically require the same fields
class RelatedLinkMixin(models.Model):
    link = models.ForeignKey(Page, null=True, blank=True, related_name='+', help_text=help_text('rca.RelatedLinkMixin', 'link'))
    link_external = models.URLField("External link", blank=True, help_text=help_text('rca.RelatedLinkMixin', 'link_external'))
    link_text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.RelatedLinkMixin', 'link_text', default="Link title (or leave blank to use page title"))

    panels = [
        PageChooserPanel('link'),
        FieldPanel('link_external'),
        FieldPanel('link_text'),
    ]

    def get_link(self):
        if self.link:
            return self.link.url
        else:
            return self.link_external

    def get_link_text(self):
        if self.link_text:
            return self.link_text
        else:
            try:
                return self.link.title
            except:
                return None

    class Meta:
        abstract = True


# == Snippet: Advert ==

class Advert(models.Model):
    page = models.ForeignKey(Page, related_name='adverts', null=True, blank=True, help_text=help_text('rca.Advert', 'page'))
    url = models.URLField(null=True, blank=True, help_text=help_text('rca.Advert', 'url'))
    text = models.CharField(max_length=255, help_text=help_text('rca.Advert', 'text', default="bold text"))
    plain_text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.Advert', 'plain_text'))
    show_globally = models.BooleanField(default=False, help_text=help_text('rca.Advert', 'show_globally'))

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
    page = ParentalKey(Page, related_name='advert_placements')
    advert = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.AdvertPlacement', 'advert'))

# == Snippet: Custom Content Module ==

class CustomContentModuleBlock(Orderable):
    content_module = ParentalKey('rca.CustomContentModule', related_name='blocks')
    link = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.CustomContentModuleBlock', 'link'))
    item_title = models.CharField(max_length=255, help_text=help_text('rca.CustomContentModuleBlock', 'item_title'))
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.CustomContentModuleBlock', 'image', default="The image for the module block"))
    text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.CustomContentModuleBlock', 'text'))

    panels = [
        PageChooserPanel('link'),
        FieldPanel('item_title'),
        ImageChooserPanel('image'),
        FieldPanel('text')
    ]

class CustomContentModule(models.Model):
    title = models.CharField(max_length=255, help_text=help_text('rca.CustomContentModule', 'title'))

    def __unicode__(self):
        return self.title

CustomContentModule.panels = [
    FieldPanel('title'),
    InlinePanel('blocks', label=""),
]

register_snippet(CustomContentModule)

class CustomeContentModulePlacement(models.Model):
    page = ParentalKey(Page, related_name='custom_content_module_placements')
    custom_content_module = models.ForeignKey('rca.CustomContentModule', related_name='+', help_text=help_text('rca.CustomeContentModulePlacement', 'custom_content_module'))

# == Snippet: Reusable rich text field ==
class ReusableTextSnippet(models.Model):
    name = models.CharField(max_length=255, help_text=help_text('rca.ReusableTextSnippet', 'name'))
    text = RichTextField(help_text=help_text('rca.ReusableTextSnippet', 'text'))
    panels = [
        FieldPanel('name'),
        FieldPanel('text', classname="full")
    ]

    def __unicode__(self):
        return self.name

register_snippet(ReusableTextSnippet)

class ReusableTextSnippetPlacement(models.Model):
    page = ParentalKey(Page, related_name='reusable_text_snippet_placements')
    reusable_text_snippet = models.ForeignKey('rca.ReusableTextSnippet', related_name='+', help_text=help_text('rca.ReusableTextSnippetPlacement', 'reusable_text_snippet'))

# == Snippet: Contacts ==

class ContactSnippetPhone(Orderable):
    page = ParentalKey('rca.ContactSnippet', related_name='contact_phone')
    phone_number = models.CharField(max_length=255, help_text=help_text('rca.ContactSnippetPhone', 'phone_number'))

    panels = [
        FieldPanel('phone_number')
    ]

class ContactSnippetEmail(Orderable):
    page = ParentalKey('rca.ContactSnippet', related_name='contact_email')
    email_address = models.CharField(max_length=255, help_text=help_text('rca.ContactSnippetEmail', 'email_address'))

    panels = [
        FieldPanel('email_address')
    ]

class ContactSnippet(models.Model):
    title = models.CharField(max_length=255, help_text=help_text('rca.ContactSnippet', 'title', default="This is the reference name for the contact. This is not displayed on the frontend."))
    contact_title = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ContactSnippet', 'contact_title', default="This is the optional title, displayed on the frontend"))
    contact_address = models.TextField(blank=True, help_text=help_text('rca.ContactSnippet', 'contact_address'))
    contact_link = models.URLField(blank=True, help_text=help_text('rca.ContactSnippet', 'contact_link'))
    contact_link_text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ContactSnippet', 'contact_link_text'))

    def __unicode__(self):
        return self.title

ContactSnippet.panels = [
    FieldPanel('title'),
    FieldPanel('contact_title'),
    FieldPanel('contact_address'),
    FieldPanel('contact_link'),
    FieldPanel('contact_link_text'),
    InlinePanel('contact_email', label="Contact phone numbers/emails"),
    InlinePanel('contact_phone', label="Contact phone number"),
]


register_snippet(ContactSnippet)

class ContactSnippetPlacement(models.Model):
    page = ParentalKey(Page, related_name='contact_snippet_placements')
    contact_snippet = models.ForeignKey('rca.ContactSnippet', related_name='+', help_text=help_text('rca.ContactSnippetPlacement', 'contact_snippet'))

# == School page ==

class SchoolPageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.SchoolPage', related_name='carousel_items')

class SchoolPageContactTelEmail(Orderable):
    page = ParentalKey('rca.SchoolPage', related_name='contact_tel_email')
    phone_number = models.CharField(max_length=255, blank=True, help_text=help_text('rca.SchoolPageContactTelEmail', 'phone_number'))
    email = models.CharField(max_length=255, blank=True, help_text=help_text('rca.SchoolPageContactTelEmail', 'email'))

    panels = [
        FieldPanel('phone_number'),
        FieldPanel('email'),
    ]

class SchoolPageContactPhone(Orderable):
    page = ParentalKey('rca.SchoolPage', related_name='contact_phone')
    phone_number = models.CharField(max_length=255, help_text=help_text('rca.SchoolPageContactPhone', 'phone_number'))

    panels = [
        FieldPanel('phone_number')
    ]

class SchoolPageContactEmail(Orderable):
    page = ParentalKey('rca.SchoolPage', related_name='contact_email')
    email_address = models.CharField(max_length=255, help_text=help_text('rca.SchoolPageContactEmail', 'email_address'))

    panels = [
        FieldPanel('email_address')
    ]

class SchoolPageRelatedLink(Orderable, RelatedLinkMixin):
    page = ParentalKey('rca.SchoolPage', related_name='related_links')

class SchoolPageAd(Orderable):
    page = ParentalKey('rca.SchoolPage', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.SchoolPageAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]


class SchoolPage(Page, SocialFields, SidebarBehaviourFields):
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, help_text=help_text('rca.SchoolPage', 'school'))
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.SchoolPage', 'background_image', default="The full bleed image in the background"))
    head_of_school = models.ForeignKey('rca.StaffPage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.SchoolPage', 'head_of_school'))
    head_of_school_statement = RichTextField(help_text=help_text('rca.SchoolPage', 'head_of_school_statement'), null=True, blank=True)
    head_of_school_link = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.SchoolPage', 'head_of_school_link'))
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.SchoolPage', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    contact_title = models.CharField(max_length=255, blank=True, help_text=help_text('rca.SchoolPage', 'contact_title'))
    contact_address = models.TextField(blank=True, help_text=help_text('rca.SchoolPage', 'contact_address'))
    contact_link = models.URLField(blank=True, help_text=help_text('rca.SchoolPage', 'contact_link'))
    contact_link_text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.SchoolPage', 'contact_link_text'))
    head_of_research = models.ForeignKey('rca.StaffPage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.SchoolPage', 'head_of_research'))
    head_of_research_statement = RichTextField(help_text=help_text('rca.SchoolPage', 'head_of_research_statement'), null=True, blank=True)
    head_of_research_link = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.SchoolPage', 'head_of_research_link'))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.SchoolPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('get_school_display'),
    )

    search_name = 'School'

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        research_items = ResearchItem.objects.filter(live=True, school=self.school).order_by('random_order')

        paginator = Paginator(research_items, 4)

        page = request.GET.get('page')
        try:
            research_items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            research_items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            research_items = paginator.page(paginator.num_pages)

        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, "rca/includes/research_listing.html", {
                'self': self,
                'research_items': research_items
            })
        else:
            return render(request, self.template, {
                'self': self,
                'research_items': research_items
            })

SchoolPage.content_panels = [
    FieldPanel('title', classname="full title"),
    ImageChooserPanel('background_image'),
    InlinePanel('carousel_items', label="Carousel content", help_text="test"),
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
    InlinePanel('contact_tel_email', label="Contact phone numbers/emails"),
    InlinePanel('contact_phone', label="Contact phone number"),
    InlinePanel('contact_email', label="Contact email"),
    PageChooserPanel('head_of_research', 'rca.StaffPage'),
    FieldPanel('head_of_research_statement', classname="full"),
    PageChooserPanel('head_of_research_link'),
    InlinePanel('related_links', label="Related links"),
    InlinePanel('manual_adverts', label="Manual adverts"),
]

SchoolPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),

    FieldPanel('school'),
]

SchoolPage.settings_panels = [
    PublishingPanel(),
    MultiFieldPanel([
        FieldPanel('collapse_upcoming_events'),
    ], 'Sidebar behaviour'),
]


# == Programme page ==

class ProgrammePageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.ProgrammePage', related_name='carousel_items')

class ProgrammePageFacilitiesCarouselItem(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='facilities_carousel_items')
    facilities_text = RichTextField(help_text=help_text('rca.ProgrammePageFacilitiesCarouselItem', 'facilities_text'), null=True, blank=True)
    facilities_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ProgrammePageFacilitiesCarouselItem', 'facilities_image'))
    facilities_link = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ProgrammePageFacilitiesCarouselItem', 'facilities_link'))

    panels = [
        ImageChooserPanel('facilities_image'),
        FieldPanel('facilities_text'),
        PageChooserPanel('facilities_link'),
    ]

class ProgrammePageManualStaffFeed(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='manual_staff_feed')
    staff = models.ForeignKey('rca.StaffPage', null=True, blank=True, related_name='+', help_text=help_text('rca.ProgrammePageManualStaffFeed', 'staff'))
    staff_role = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ProgrammePageManualStaffFeed', 'staff_role'))

    panels = [
        PageChooserPanel('staff', 'rca.StaffPage'),
        FieldPanel('staff_role'),
    ]

class ProgrammePageRelatedLink(Orderable, RelatedLinkMixin):
    page = ParentalKey('rca.ProgrammePage', related_name='related_links')

class ProgrammePageContactPhone(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='contact_phone')
    phone_number = models.CharField(max_length=255, help_text=help_text('rca.ProgrammePageContactPhone', 'phone_number'))

    panels = [
        FieldPanel('phone_number')
    ]

class ProgrammePageContactEmail(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='contact_email')
    email_address = models.CharField(max_length=255, help_text=help_text('rca.ProgrammePageContactEmail', 'email_address'))

    panels = [
        FieldPanel('email_address')
    ]

class ProgrammePageOurSites(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='our_sites')
    url = models.URLField(help_text=help_text('rca.ProgrammePageOurSites', 'url'))
    site_name = models.CharField(max_length=255, help_text=help_text('rca.ProgrammePageOurSites', 'site_name'))
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ProgrammePageOurSites', 'image'))

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('url'),
        FieldPanel('site_name')
    ]

class ProgrammeDocuments(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='documents')
    document = models.ForeignKey('wagtaildocs.Document', null=True, blank=True, related_name='+', help_text=help_text('rca.ProgrammeDocuments', 'document'))
    text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ProgrammeDocuments', 'text'))

    panels = [
        DocumentChooserPanel('document'),
        FieldPanel('text')
    ]

class ProgrammePageStudentStory(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='student_stories')
    name = models.CharField(max_length=255, help_text=help_text('rca.ProgrammePageStudentStory', 'name'))
    text = RichTextField(help_text=help_text('rca.ProgrammePageStudentStory', 'text'))
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ProgrammePageStudentStory', 'image'))
    link = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ProgrammePageStudentStory', 'link'))

    panels = [
        FieldPanel('name'),
        FieldPanel('text'),
        ImageChooserPanel('image'),
        PageChooserPanel('link'),
    ]

class ProgrammePageAd(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.ProgrammePageAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]


class ProgrammePageProgramme(models.Model):
    page = ParentalKey('rca.ProgrammePage', related_name='programmes')
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True, help_text=help_text('rca.ProgrammePageProgramme', 'programme'))

    panels = [FieldPanel('programme')]


class ProgrammePage(Page, SocialFields, SidebarBehaviourFields):
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, help_text=help_text('rca.ProgrammePage', 'school'))
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ProgrammePage', 'background_image', default="The full bleed image in the background"))
    head_of_programme = models.ForeignKey('rca.StaffPage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ProgrammePage', 'head_of_programme', default="Select the profile page of the head of this programme."))
    head_of_programme_second = models.ForeignKey('rca.StaffPage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', verbose_name="Second head of programme", help_text=help_text('rca.ProgrammePage', 'head_of_programme_secondary', default="Select the profile page of another head of this programme."))
    head_of_programme_statement = RichTextField("Head(s) of programme statement", help_text=help_text('rca.ProgrammePage', 'head_of_programme_statement'), null=True, blank=True)
    head_of_programme_link = models.ForeignKey(Page, verbose_name="Head(s) of programme link", null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ProgrammePage', 'head_of_programme_link', default="The link to the Head(s) of Programme Welcome Page"))
    programme_video = models.CharField('Programme video Vimeo address', max_length=255, blank=True, help_text=help_text('rca.ProgrammePage', 'programme_video', default="The web addres for the programme video on Vimeo. For example, 'http://vimeo.com/62715625'."))
    programme_video_poster_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ProgrammePage', 'programme_video_poster_image', default="The poster image for the programme video"))
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ProgrammePage', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    contact_title = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ProgrammePage', 'contact_title'))
    contact_address = models.TextField(blank=True, help_text=help_text('rca.ProgrammePage', 'contact_address'))
    contact_link = models.URLField(blank=True, help_text=help_text('rca.ProgrammePage', 'contact_link'))
    contact_link_text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ProgrammePage', 'contact_link_text'))
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ProgrammePage', 'twitter_feed', default="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term"))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ProgrammePage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    # TO BE DELETED
    facilities_text = RichTextField(editable=False, null=True, blank=True,)
    facilities_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', editable=False)
    facilities_link = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL, related_name='+', editable=False)

    search_fields = Page.search_fields + (
        index.SearchField('get_programme_display'),
        index.SearchField('get_school_display'),
    )

    search_name = 'Programme'

    def get_programme_display(self):
        programmes = ProgrammePageProgramme.objects\
            .filter(page=self)\
            .only('programme')\
            .distinct()\
            .values_list('programme', flat=True)
        programme_labels = dict(ALL_PROGRAMMES)
        return ", ".join([programme_labels[p] for p in programmes])

    @property
    def staff_feed(self):
        # Get staff from manual feed
        feed = self.manual_staff_feed.all()

        # Get each staffpage out of the feed and add their role
        feed2 = []
        for staffpage in feed:
            staff = staffpage.staff
            staff.staff_role = staffpage.staff_role
            feed2.append(staff)

        return feed2

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        programmes = [p.programme for p in self.programmes.all()]
        research_items = ResearchItem.objects.filter(live=True, programme__in=programmes).order_by('random_order')

        per_page = 4
        paginator = Paginator(research_items, per_page)

        page = request.GET.get('page')
        try:
            research_items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            research_items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            research_items = paginator.page(paginator.num_pages)

        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, "rca/includes/research_listing.html", {
                'self': self,
                'research_items': research_items,
                'per_page': per_page,
            })
        else:
            return render(request, self.template, {
                'self': self,
                'research_items': research_items,
                'per_page': per_page,
            })

ProgrammePage.content_panels = [
    FieldPanel('title', classname="full title"),
    ImageChooserPanel('background_image'),
    InlinePanel('carousel_items', label="Carousel content"),
    MultiFieldPanel([
        PageChooserPanel('head_of_programme', 'rca.StaffPage',),
        PageChooserPanel('head_of_programme_second', 'rca.StaffPage',),
        FieldPanel('head_of_programme_statement', classname="full"),
        PageChooserPanel('head_of_programme_link'),
    ], 'Head of Programme details'),
    InlinePanel('manual_staff_feed', label="Manual staff feed"),
    InlinePanel('our_sites', label="Our sites"),
    MultiFieldPanel([
        FieldPanel('programme_video'),
        ImageChooserPanel('programme_video_poster_image'),
    ], 'Programme video'),
    InlinePanel('student_stories', label="Student stories"),
    InlinePanel('facilities_carousel_items', label="Facilities"),
    InlinePanel('documents', label="Documents"),
    InlinePanel('related_links', label="Related links"),
    InlinePanel('manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
    MultiFieldPanel([
        FieldPanel('contact_title'),
        FieldPanel('contact_address'),
        FieldPanel('contact_link'),
        FieldPanel('contact_link_text'),
    ], 'Contact'),
    InlinePanel('contact_phone', label="Contact phone number"),
    InlinePanel('contact_email', label="Contact email"),
]

ProgrammePage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),

    FieldPanel('school'),

    # TODO: can't enforce the minumum number of inlines just yet: https://github.com/torchbox/wagtail/issues/669
    InlinePanel('programmes', label="Programmes (*at least one is required)"),
]

ProgrammePage.settings_panels = [
    PublishingPanel(),
    MultiFieldPanel([
        FieldPanel('collapse_upcoming_events'),
    ], 'Sidebar behaviour'),
]

# == News Index ==

class NewsIndexAd(Orderable):
    page = ParentalKey('rca.NewsIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.NewsIndexAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class NewsIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.NewsIndex', 'intro'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewsIndex', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.NewsIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))
    subpage_types = ['NewsItem']

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
    )

    search_name = None

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        programme = request.GET.get('programme')
        school = request.GET.get('school')
        area = request.GET.get('area')

        news = NewsItem.objects.filter(live=True, path__startswith=self.path, show_on_news_index=True)

        # Run school and programme filters
        news, filters = run_filters(news, [
            ('school', 'related_schools__school', school),
            ('programme', 'related_programmes__programme', programme),
            ('areas', 'areas__area', area)
        ])

        news = news.distinct().order_by('-date')

        page = request.GET.get('page')
        paginator = Paginator(news, 10)  # Show 10 news items per page
        try:
            news = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            news = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver lst page of results.
            news = paginator.page(paginator.num_pages)

        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, "rca/includes/news_listing.html", {
                'self': self,
                'news': news,
                'filters': json.dumps(filters),
            })
        else:
            return render(request, self.template, {
                'self': self,
                'news': news,
                'filters': json.dumps(filters),
            })

NewsIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel('manual_adverts', label="Manual adverts"),
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
        FieldPanel('search_description'),
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
    link = models.URLField(help_text=help_text('rca.NewsItemLink', 'link'))
    link_text = models.CharField(max_length=255, help_text=help_text('rca.NewsItemLink', 'link_text'))

    panels=[
        FieldPanel('link'),
        FieldPanel('link_text')
    ]

class NewsItemRelatedSchool(models.Model):
    page = ParentalKey('rca.NewsItem', related_name='related_schools')
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True, help_text=help_text('rca.NewsItemRelatedSchool', 'school'))

    panels = [
        FieldPanel('school')
    ]

class NewsItemRelatedProgramme(models.Model):
    page = ParentalKey('rca.NewsItem', related_name='related_programmes')
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True, help_text=help_text('rca.NewsItemRelatedProgramme', 'programme'))

    panels = [FieldPanel('programme')]

class NewsItemArea(models.Model):
    page = ParentalKey('rca.NewsItem', related_name='areas')
    area = models.CharField(max_length=255, choices=AREA_CHOICES, help_text=help_text('rca.NewsItemArea', 'area'))

    panels = [FieldPanel('area')]

class NewsItem(Page, SocialFields):
    author = models.CharField(max_length=255, help_text=help_text('rca.NewsItem', 'author'))
    date = models.DateField(help_text=help_text('rca.NewsItem', 'date'))
    intro = RichTextField(help_text=help_text('rca.NewsItem', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.NewsItem', 'body'))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.NewsItem', 'show_on_homepage'))
    show_on_news_index = models.BooleanField(default=True, help_text=help_text('rca.NewsItem', 'show_on_news_index'))
    listing_intro = models.CharField(max_length=100, blank=True, help_text=help_text('rca.NewsItem', 'listing_intro', default="Used only on pages listing news items"))
    rca_content_id = models.CharField(max_length=255, blank=True, editable=False) # for import
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.NewsItem', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))
    # TODO: Embargo Date, which would perhaps be part of a workflow module, not really a model thing?

    # DELETED FIELDS
    area = models.CharField(max_length=255, choices=AREA_CHOICES, blank=True, editable=False, help_text=help_text('rca.NewsItem', 'area'))

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
        index.SearchField('body'),
    )

    search_name = 'News'

    def get_related_news(self, count=4):
        return NewsItem.get_related(
            areas=list(self.areas.values_list('area', flat=True)),
            programmes=list(self.related_programmes.values_list('programme', flat=True)),
            schools=list(self.related_schools.values_list('school', flat=True)),
            exclude=self,
            count=count
        )

    @staticmethod
    def get_related(areas=None, programmes=None, schools=None, exclude=None, count=4):
        """
            Get NewsItem objects that have the highest relevance to the specified
            areas (multiple), programmes (multiple) and schools (multiple).
        """

        # Assign each news item a score indicating similarity to these params:
        # 100 points for a matching area, 10 points for a matching programme,
        # 1 point for a matching school.

        # if self.area is blank, we don't want to give priority to other news items
        # that also have a blank area field - so instead, set the target area to
        # something that will never match, so that it never contributes to the score
        if not areas:
            areas = ["this_will_never_match"]

        if not programmes:
            # insert a dummy programme name to avoid an empty IN clause
            programmes = ["this_will_never_match_either"]

        if not schools:
            # insert a dummy school name to avoid an empty IN clause
            schools = ["this_will_never_match_either"]

        results = NewsItem.objects.extra(
            select={'score': """
                (
                    SELECT COUNT(*) FROM rca_newsitemarea
                    WHERE rca_newsitemarea.page_id=wagtailcore_page.id
                        AND rca_newsitemarea.area IN %s
                ) * 100
                + (
                    SELECT COUNT(*) FROM rca_newsitemrelatedprogramme
                    WHERE rca_newsitemrelatedprogramme.page_id=wagtailcore_page.id
                        AND rca_newsitemrelatedprogramme.programme IN %s
                ) * 10
                + (
                    SELECT COUNT(*) FROM rca_newsitemrelatedschool
                    WHERE rca_newsitemrelatedschool.page_id=wagtailcore_page.id
                        AND rca_newsitemrelatedschool.school IN %s
                ) * 1
            """},
            select_params=(tuple(areas), tuple(programmes), tuple(schools))
        )
        if exclude:
            results = results.exclude(id=exclude.id)

        # Only show live results
        results = results.filter(live=True)

        return results.order_by('-score')[:count]


NewsItem.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('author'),
    FieldPanel('date'),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    InlinePanel('related_links', label="Links"),
    InlinePanel('carousel_items', label="Carousel content"),
]

NewsItem.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_on_homepage'),
        FieldPanel('listing_intro'),
        ImageChooserPanel('feed_image'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),

    FieldPanel('show_on_news_index'),
    InlinePanel('areas', label="Areas"),
    InlinePanel('related_schools', label="Related schools"),
    InlinePanel('related_programmes', label="Related programmes"),
]

# == Press Release Index ==

class PressReleaseIndexAd(Orderable):
    page = ParentalKey('rca.PressReleaseIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.PressReleaseIndexAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class PressReleaseIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.PressReleaseIndex', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.PressReleaseIndex', 'body'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.PressReleaseIndex', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.PressReleaseIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
        index.SearchField('body'),
    )

    search_name = None

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        press_releases = PressRelease.objects.filter(live=True).order_by('-date')

        page = request.GET.get('page')
        paginator = Paginator(press_releases, 10)  # Show 10 press_releases items per page
        try:
            press_releases = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            press_releases = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            press_releases = paginator.page(paginator.num_pages)

        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, "rca/includes/press_release_listing.html", {
                'self': self,
                'press_releases': press_releases,
            })
        else:
            return render(request, self.template, {
                'self': self,
                'press_releases': press_releases,
            })

PressReleaseIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    InlinePanel('manual_adverts', label="Manual adverts"),
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
        FieldPanel('search_description'),
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
    link = models.URLField(help_text=help_text('rca.PressReleaseLink', 'link'))
    link_text = models.CharField(max_length=255, help_text=help_text('rca.PressReleaseLink', 'link_text'))

    panels=[
        FieldPanel('link'),
        FieldPanel('link_text')
    ]

class PressReleaseRelatedSchool(models.Model):
    page = ParentalKey('rca.PressRelease', related_name='related_schools')
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True, help_text=help_text('rca.PressReleaseRelatedSchool', 'school'))

    panels = [
        FieldPanel('school')
    ]

class PressReleaseRelatedProgramme(models.Model):
    page = ParentalKey('rca.PressRelease', related_name='related_programmes')
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True, help_text=help_text('rca.PressReleaseRelatedProgramme', 'programme'))

    panels = [FieldPanel('programme')]

class PressReleaseArea(models.Model):
    page = ParentalKey('rca.PressRelease', related_name='areas')
    area = models.CharField(max_length=255, choices=AREA_CHOICES, help_text=help_text('rca.PressReleaseArea', 'area'))

    panels = [FieldPanel('area')]

class PressRelease(Page, SocialFields):
    author = models.CharField(max_length=255, help_text=help_text('rca.PressRelease', 'author'))
    date = models.DateField(help_text=help_text('rca.PressRelease', 'date'))
    intro = RichTextField(help_text=help_text('rca.PressRelease', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.PressRelease', 'body'))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.PressRelease', 'show_on_homepage'))
    listing_intro = models.CharField(max_length=100, blank=True, help_text=help_text('rca.PressRelease', 'listing_intro', default="Used only on pages listing news items"))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.PressRelease', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))
    # TODO: Embargo Date, which would perhaps be part of a workflow module, not really a model thing?

    # DELETED FIELDS
    area = models.CharField(max_length=255, choices=AREA_CHOICES, blank=True, editable=False, help_text=help_text('rca.PressRelease', 'area'))

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
        index.SearchField('body'),
    )

    search_name = 'PressRelease'


PressRelease.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('author'),
    FieldPanel('date'),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    InlinePanel('related_links', label="Links"),
    InlinePanel('carousel_items', label="Carousel content"),
]

PressRelease.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_on_homepage'),
        FieldPanel('listing_intro'),
        ImageChooserPanel('feed_image'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),

    InlinePanel('areas', label="Areas"),
    InlinePanel('related_schools', label="Related schools"),
    InlinePanel('related_programmes', label="Related programmes"),
]


# == Event Item ==

class EventItemSpeaker(Orderable):
    page = ParentalKey('rca.EventItem', related_name='speakers')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.EventItemSpeaker', 'image'))
    name = models.CharField(max_length=255, help_text=help_text('rca.EventItemSpeaker', 'name'))
    surname = models.CharField(max_length=255, help_text=help_text('rca.EventItemSpeaker', 'surname'))
    link_page = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.EventItemSpeaker', 'link_page'))
    link = models.URLField(blank=True, help_text=help_text('rca.EventItemSpeaker', 'link'))

    panels=[
        FieldPanel('name'),
        FieldPanel('surname'),
        ImageChooserPanel('image'),
        PageChooserPanel('link_page'),
        FieldPanel('link'),
    ]


class EventItemCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.EventItem', related_name='carousel_items')

class EventItemScreen(models.Model):
    page = ParentalKey('rca.EventItem', related_name='screens')
    screen = models.CharField(max_length=255, choices=SCREEN_CHOICES, blank=True, help_text=help_text('rca.EventItemScreen', 'screen'))

    panels = [FieldPanel('screen')]

class EventItemRelatedSchool(models.Model):
    page = ParentalKey('rca.EventItem', related_name='related_schools')
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True, help_text=help_text('rca.EventItemRelatedSchool', 'school'))

    panels = [FieldPanel('school')]

class EventItemRelatedProgramme(models.Model):
    page = ParentalKey('rca.EventItem', related_name='related_programmes')
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True, help_text=help_text('rca.EventItemRelatedProgramme', 'programme'))

    panels = [FieldPanel('programme')]

class EventItemRelatedArea(models.Model):
    page = ParentalKey('rca.EventItem', related_name='related_areas')
    area = models.CharField(max_length=255, choices=EVENT_AREA_CHOICES, blank=True, help_text=help_text('rca.EventItemRelatedArea', 'area'))

    panels = [FieldPanel('area')]

class EventItemContactPhone(Orderable):
    page = ParentalKey('rca.EventItem', related_name='contact_phone')
    phone_number = models.CharField(max_length=255, help_text=help_text('rca.EventItemContactPhone', 'phone_number'))

    panels = [
        FieldPanel('phone_number')
    ]

class EventItemContactEmail(Orderable):
    page = ParentalKey('rca.EventItem', related_name='contact_email')
    email_address = models.CharField(max_length=255, help_text=help_text('rca.EventItemContactEmail', 'email_address'))

    panels = [
        FieldPanel('email_address')
    ]

class EventItemDatesTimes(Orderable):
    page = ParentalKey('rca.EventItem', related_name='dates_times')
    date_from = models.DateField("Start date", help_text=help_text('rca.EventItemDatesTimes', 'date_from'))
    date_to = models.DateField("End date", null=True, blank=True, help_text=help_text('rca.EventItemDatesTimes', 'date_to', default="Not required if event is on a single day"))
    time_from = models.TimeField("Start time", null=True, blank=True, help_text=help_text('rca.EventItemDatesTimes', 'time_from'))
    time_to = models.TimeField("End time", null=True, blank=True, help_text=help_text('rca.EventItemDatesTimes', 'time_to'))
    time_other = models.CharField("Time other", max_length=255, blank=True, help_text=help_text('rca.EventItemDatesTimes', 'time_other', default="Use this field to give additional information about start and end times"))

    panels = [
        FieldPanel('date_from'),
        FieldPanel('date_to'),
        FieldPanel('time_from'),
        FieldPanel('time_to'),
        FieldPanel('time_other'),
    ]

class EventItemExternalLink(Orderable):
    page = ParentalKey('rca.EventItem', related_name='external_links')
    link = models.URLField(help_text=help_text('rca.EventItemExternalLink', 'link'))
    text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.EventItemExternalLink', 'text'))

    panels = [
        FieldPanel('link'),
        FieldPanel('text'),
    ]

class FutureEventItemManager(models.Manager):
    def get_queryset(self):
        return super(FutureEventItemManager, self).get_queryset().extra(
            where=["wagtailcore_page.id IN (SELECT DISTINCT page_id FROM rca_eventitemdatestimes WHERE date_from >= %s OR date_to >= %s)"],
            params=[date.today(), date.today()]
        )

class FutureNotCurrentEventItemManager(models.Manager):
    def get_queryset(self):
        return super(FutureNotCurrentEventItemManager, self).get_queryset().extra(
            where=["wagtailcore_page.id IN (SELECT DISTINCT page_id FROM rca_eventitemdatestimes WHERE date_from >= %s)"],
            params=[date.today()]
        ).extra(
            select={'next_date_from': '(SELECT date_from FROM rca_eventitemdatestimes WHERE page_id=wagtailcore_page.id AND date_from >= %s LIMIT 1)'},
            select_params=[date.today()],
            order_by=['next_date_from']
        )

class PastEventItemManager(models.Manager):
    def get_queryset(self):
        return super(PastEventItemManager, self).get_queryset().extra(
            where=["wagtailcore_page.id NOT IN (SELECT DISTINCT page_id FROM rca_eventitemdatestimes WHERE date_from >= %s OR date_to >= %s)"],
            params=[date.today(), date.today()]
        )

class EventItem(Page, SocialFields):
    body = RichTextField(help_text=help_text('rca.EventItem', 'body'))
    audience = models.CharField(max_length=255, choices=EVENT_AUDIENCE_CHOICES, help_text=help_text('rca.EventItem', 'audience'))
    area = models.CharField(max_length=255, choices=EVENT_AREA_CHOICES, blank=True, help_text=help_text('rca.EventItem', 'area'))
    location = models.CharField(max_length=255, choices=EVENT_LOCATION_CHOICES, help_text=help_text('rca.EventItem', 'location'))
    location_other = models.CharField("'Other' location", max_length=255, blank=True, help_text=help_text('rca.EventItem', 'location_other'))
    specific_directions = models.CharField(max_length=255, blank=True, help_text=help_text('rca.EventItem', 'specific_directions', default="Brief, more specific location e.g Go to reception on 2nd floor"))
    specific_directions_link = models.URLField(blank=True, help_text=help_text('rca.EventItem', 'specific_directions_link'))
    gallery = models.CharField("RCA galleries and rooms", max_length=255, choices=EVENT_GALLERY_CHOICES, blank=True, help_text=help_text('rca.EventItem', 'gallery'))
    special_event = models.BooleanField("Highlight as special event on signage", default=False, help_text=help_text('rca.EventItem', 'special_event', default="Toggling this is a quick way to remove/add an event from signage without deleting the screens defined below"))
    cost = RichTextField(help_text=help_text('rca.EventItem', 'cost'), blank=True)
    eventbrite_id = models.CharField(max_length=255, blank=True, help_text=help_text('rca.EventItem', 'eventbrite_id', default="Must be a ten-digit number. You can find for you event ID by logging on to Eventbrite, then going to the Manage page for your event. Once on the Manage page, look in the address bar of your browser for eclass=XXXXXXXXXX. This ten-digit number after eclass= is the event ID."))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.EventItem', 'show_on_homepage'))
    listing_intro = models.CharField(max_length=100, blank=True, help_text=help_text('rca.EventItem', 'listing_intro', default="Used only on pages listing event items"))
    middle_column_body = RichTextField(blank=True, help_text=help_text('rca.EventItem', 'middle_column_body',))
    contact_title = models.CharField(max_length=255, blank=True, help_text=help_text('rca.EventItem', 'contact_title'))
    contact_address = models.TextField(blank=True, help_text=help_text('rca.EventItem', 'contact_address'))
    contact_link = models.URLField(blank=True, help_text=help_text('rca.EventItem', 'contact_link'))
    contact_link_text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.EventItem', 'contact_link_text'))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.EventItem', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))
    # TODO: Embargo Date, which would perhaps be part of a workflow module, not really a model thing?

    # DELETED
    external_link = models.URLField(blank=True, editable=False)
    external_link_text = models.CharField(max_length=255, blank=True, editable=False)

    objects = models.Manager()
    future_objects = FutureEventItemManager()
    past_objects = PastEventItemManager()
    future_not_current_objects = FutureNotCurrentEventItemManager()

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
        index.SearchField('get_location_display'),
        index.SearchField('location_other'),
    )

    search_name = 'Event'

    @property
    def next_date_time(self):
        return self.dates_times.order_by('date_from').filter(date_from__gte=timezone.now().date).first()

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
                            'UID:' + hashlib.sha1(self.url + str(start_datetime)).hexdigest() + '@rca.ac.uk',
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
        InlinePanel('external_links', label="External links"),
        FieldPanel('middle_column_body')
    ], 'Event detail'),
    FieldPanel('body', classname="full"),
    InlinePanel('dates_times', label="Dates and times"),
    InlinePanel('speakers', label="Speaker"),
    InlinePanel('carousel_items', label="Carousel content"),
    MultiFieldPanel([
        FieldPanel('contact_title'),
        FieldPanel('contact_address'),
        FieldPanel('contact_link'),
        FieldPanel('contact_link_text'),
    ],'Contact'),
    InlinePanel('contact_phone', label="Contact phone number"),
    InlinePanel('contact_email', label="Contact email address"),
]

EventItem.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_on_homepage'),
        FieldPanel('listing_intro'),
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),

    MultiFieldPanel([
        FieldPanel('special_event'),
        InlinePanel('screens', label="Screen on which to highlight"),
        ], 'Special event signage'),
    InlinePanel('related_schools', label="Related schools"),
    InlinePanel('related_programmes', label="Related programmes"),
    InlinePanel('related_areas', label="Related areas"),
]


# == Event index ==

class EventIndexRelatedLink(Orderable, RelatedLinkMixin):
    page = ParentalKey('rca.EventIndex', related_name='related_links')

class EventIndexAd(Orderable):
    page = ParentalKey('rca.EventIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.EventIndexAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class EventIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.EventIndex', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.EventIndex', 'body'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.EventIndex', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.EventIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
        index.SearchField('body'),
    )

    search_name = None

    def future_events(self):
        return EventItem.future_objects.filter(live=True, path__startswith=self.path)

    def past_events(self):
        return EventItem.past_objects.filter(live=True, path__startswith=self.path)

    @vary_on_headers('X-Requested-With')
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

        # Run filters
        events, filters = run_filters(events, [
            ('school', 'related_schools__school', school),
            ('programme', 'related_programmes__programme', programme),
            ('location', 'location', location),
            ('area', 'related_areas__area', area),
            ('audience', 'audience', audience),
        ])

        events = events.annotate(start_date=Min('dates_times__date_from'), end_date=Max('dates_times__date_to'))
        if period== 'past':
            events = events.order_by('start_date').reverse()
        else:
            events = events.order_by('start_date')

        events = events.distinct()

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

        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, "rca/includes/events_listing.html", {
                'self': self,
                'events': events,
                'filters': json.dumps(filters),
            })
        else:
            return render(request, self.template, {
                'self': self,
                'events': events,
                'filters': json.dumps(filters),
            })

EventIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    InlinePanel('related_links', label="Related links"),
    InlinePanel('manual_adverts', label="Manual adverts"),
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
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]

# == Talks index ==


class TalksIndexAd(Orderable):
    page = ParentalKey('rca.TalksIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.TalksIndexAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class TalksIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.TalksIndex', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.TalksIndex', 'body'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.TalksIndex', 'twitter_feed', default="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term"))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.TalksIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
        index.SearchField('body'),
    )

    search_page = None

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        talks = EventItem.past_objects.filter(live=True, audience='rcatalks').annotate(start_date=Min('dates_times__date_from')).order_by('-start_date')

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

        if request.is_ajax() and 'pjax' not in request.GET:
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
    FieldPanel('body', classname="full"),
    InlinePanel('manual_adverts', label="Manual adverts"),
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
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]



# == Reviews index ==


class ReviewsIndexAd(Orderable):
    page = ParentalKey('rca.ReviewsIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.ReviewsIndexAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class ReviewsIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.ReviewsIndex', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.ReviewsIndex', 'body'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ReviewsIndex', 'twitter_feed', default="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term"))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ReviewsIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
        index.SearchField('body'),
    )

    search_name = None

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        reviews = ReviewPage.objects.filter(live=True)
        reviews = reviews.distinct()
        reviews = reviews.order_by('-date')

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

        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, "rca/includes/reviews_listing.html", {
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
    FieldPanel('body', classname="full"),
    InlinePanel('manual_adverts', label="Manual adverts"),
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
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]


# == Review page ==

class ReviewPageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.ReviewPage', related_name='carousel_items')

class ReviewPageRelatedLink(Orderable, RelatedLinkMixin):
    page = ParentalKey('rca.ReviewPage', related_name='related_links')

class ReviewPageQuotation(Orderable):
    page = ParentalKey('rca.ReviewPage', related_name='quotations')
    quotation = models.TextField(help_text=help_text('rca.ReviewPageQuotation', 'quotation'))
    quotee = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ReviewPageQuotation', 'quotee'))
    quotee_job_title = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ReviewPageQuotation', 'quotee_job_title'))

    panels = [
        FieldPanel('quotation'),
        FieldPanel('quotee'),
        FieldPanel('quotee_job_title')
    ]

class ReviewPageRelatedDocument(Orderable):
    page = ParentalKey('rca.ReviewPage', related_name='documents')
    document = models.ForeignKey('wagtaildocs.Document', null=True, blank=True, related_name='+', help_text=help_text('rca.ReviewPageRelatedDocument', 'document'))
    document_name = models.CharField(max_length=255, help_text=help_text('rca.ReviewPageRelatedDocument', 'document_name'))

    panels = [
        DocumentChooserPanel('document'),
        FieldPanel('document_name')
    ]

class ReviewPageImage(Orderable):
    page = ParentalKey('rca.ReviewPage', related_name='images')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+', help_text=help_text('rca.ReviewPageImage', 'image'))

    panels = [
        ImageChooserPanel('image'),
    ]

class ReviewPageAd(Orderable):
    page = ParentalKey('rca.ReviewPage', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.ReviewPageAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class ReviewPage(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.ReviewPage', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.ReviewPage', 'body'))
    strapline = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ReviewPage', 'strapline'))
    middle_column_body = RichTextField(blank=True, help_text=help_text('rca.ReviewPage', 'middle_column_body'))
    date = models.DateField(null=True, blank=True, help_text=help_text('rca.ReviewPage', 'date'))
    author = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ReviewPage', 'author'))
    listing_intro = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ReviewPage', 'listing_intro', default="Used only on pages listing jobs"))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.ReviewPage', 'show_on_homepage'))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ReviewPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('body'),
        index.SearchField('strapline'),
        index.SearchField('author'),
    )

    search_name = 'Review'

ReviewPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('strapline', classname="full"),
    FieldPanel('author'),
    FieldPanel('date'),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    InlinePanel('carousel_items', label="Carousel content"),
    InlinePanel('related_links', label="Related links"),
    FieldPanel('middle_column_body', classname="full"),
    InlinePanel('documents', label="Document"),
    InlinePanel('quotations', label="Quotation"),
    InlinePanel('images', label="Middle column image"),
    InlinePanel('manual_adverts', label="Manual adverts"),
]

ReviewPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_on_homepage'),
        ImageChooserPanel('feed_image'),
        FieldPanel('listing_intro'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]

# == Standard page ==

class StandardPageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.StandardPage', related_name='carousel_items')

class StandardPageRelatedLink(Orderable, RelatedLinkMixin):
    page = ParentalKey('rca.StandardPage', related_name='related_links')

class StandardPageQuotation(Orderable):
    page = ParentalKey('rca.StandardPage', related_name='quotations')
    quotation = models.TextField(help_text=help_text('rca.StandardPageQuotation', 'quotation'))
    quotee = models.CharField(max_length=255, blank=True, help_text=help_text('rca.StandardPageQuotation', 'quotee'))
    quotee_job_title = models.CharField(max_length=255, blank=True, help_text=help_text('rca.StandardPageQuotation', 'quotee_job_title'))

    panels = [
        FieldPanel('quotation'),
        FieldPanel('quotee'),
        FieldPanel('quotee_job_title')
    ]

class StandardPageRelatedDocument(Orderable):
    page = ParentalKey('rca.StandardPage', related_name='documents')
    document = models.ForeignKey('wagtaildocs.Document', null=True, blank=True, related_name='+', help_text=help_text('rca.StandardPageRelatedDocument', 'document'))
    document_name = models.CharField(max_length=255, help_text=help_text('rca.StandardPageRelatedDocument', 'document_name'))

    panels = [
        DocumentChooserPanel('document'),
        FieldPanel('document_name')
    ]

class StandardPageImage(Orderable):
    page = ParentalKey('rca.StandardPage', related_name='images')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+', help_text=help_text('rca.StandardPageImage', 'image'))

    panels = [
        ImageChooserPanel('image'),
    ]

class StandardPageAd(Orderable):
    page = ParentalKey('rca.StandardPage', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.StandardPageAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class StandardPageReusableTextSnippet(Orderable):
    page = ParentalKey('rca.StandardPage', related_name='reusable_text_snippets')
    reusable_text_snippet = models.ForeignKey('rca.ReusableTextSnippet', related_name='+', help_text=help_text('rca.StandardPageReusableTextSnippet', 'reusable_text_snippet'))

    panels = [
        SnippetChooserPanel('reusable_text_snippet', ReusableTextSnippet),
    ]

class StandardPageTag(TaggedItemBase):
    content_object = ParentalKey('rca.StandardPage', related_name='tagged_items')

class StandardPage(Page, SocialFields, SidebarBehaviourFields):
    intro = RichTextField(help_text=help_text('rca.StandardPage', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.StandardPage', 'body'))
    strapline = models.CharField(max_length=255, blank=True, help_text=help_text('rca.StandardPage', 'strapline'))
    middle_column_body = RichTextField(blank=True, help_text=help_text('rca.StandardPage', 'middle_column_body'))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.StandardPage', 'show_on_homepage'))
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.StandardPage', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    related_school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True, help_text=help_text('rca.StandardPage', 'related_school'))
    related_programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True, help_text=help_text('rca.StandardPage', 'related_programme'))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.StandardPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))
    tags = ClusterTaggableManager(through=StandardPageTag, help_text=help_text('rca.StandardPage', 'tags'))

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
        index.SearchField('body'),
    )

    # StandardPages with a STUDENT_STORY_TAG or ALUMNI_STORY_TAG can be listed on the homepage packery separately.
    # TODO: This can be done more elegantly with proxy models. See related PR here: https://github.com/torchbox/wagtail/pull/1736/files
    STUDENT_STORY_TAG = 'student-story'
    ALUMNI_STORY_TAG = 'alumni-story'

    @property
    def search_name(self):
        if self.related_programme:
            return self.get_related_programme_display()

        if self.related_school:
            return self.get_related_school_display()

        return None

StandardPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('strapline', classname="full"),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    InlinePanel('carousel_items', label="Carousel content"),
    InlinePanel('related_links', label="Related links"),
    FieldPanel('middle_column_body', classname="full"),
    InlinePanel('reusable_text_snippets', label="Reusable text snippet"),
    InlinePanel('documents', label="Document"),
    InlinePanel('quotations', label="Quotation"),
    InlinePanel('images', label="Middle column image"),
    InlinePanel('manual_adverts', label="Manual adverts"),
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
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),

    MultiFieldPanel([
        FieldPanel('related_school'),
        FieldPanel('related_programme'),
    ], 'Related pages'),
    FieldPanel('tags'),
]

StandardPage.settings_panels = [
    PublishingPanel(),
    MultiFieldPanel([
        FieldPanel('collapse_upcoming_events'),
    ], 'Sidebar behaviour'),
]

# == Standard Index page ==

class StandardIndexCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.StandardIndex', related_name='carousel_items')

class StandardIndexTeaser(Orderable):
    page = ParentalKey('rca.StandardIndex', related_name='teasers')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.StandardIndexTeaser', 'image'))
    link = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.StandardIndexTeaser', 'link'))
    external_link = models.URLField(blank=True, help_text="Used only if the (internal) link above is not defined.")
    title = models.CharField(max_length=255, blank=True, help_text=help_text('rca.StandardIndexTeaser', 'title'))
    text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.StandardIndexTeaser', 'text'))

    panels = [
        ImageChooserPanel('image'),
        PageChooserPanel('link'),
        FieldPanel('external_link'),
        FieldPanel('title', classname="full title"),
        FieldPanel('text'),
    ]

class StandardIndexStaffFeed(Orderable):
    page = ParentalKey('rca.StandardIndex', related_name='manual_staff_feed')
    staff = models.ForeignKey('rca.StaffPage', null=True, blank=True, related_name='+', help_text=help_text('rca.StandardIndexStaffFeed', 'staff'))
    staff_role = models.CharField(max_length=255, blank=True, help_text=help_text('rca.StandardIndexStaffFeed', 'staff_role'))

    panels = [
        PageChooserPanel('staff', 'rca.StaffPage'),
        FieldPanel('staff_role'),
    ]

class StandardIndexRelatedLink(Orderable, RelatedLinkMixin):
    page = ParentalKey('rca.StandardIndex', related_name='related_links')

class StandardIndexContactPhone(Orderable):
    page = ParentalKey('rca.StandardIndex', related_name='contact_phone')
    phone_number = models.CharField(max_length=255, help_text=help_text('rca.StandardIndexContactPhone', 'phone_number'))

    panels = [
        FieldPanel('phone_number')
    ]

class StandardIndexContactEmail(Orderable):
    page = ParentalKey('rca.StandardIndex', related_name='contact_email')
    email_address = models.CharField(max_length=255, help_text=help_text('rca.StandardIndexContactEmail', 'email_address'))

    panels = [
        FieldPanel('email_address')
    ]

class StandardIndexOurSites(Orderable):
    page = ParentalKey('rca.StandardIndex', related_name='our_sites')
    url = models.URLField(help_text=help_text('rca.StandardIndexOurSites', 'url'))
    site_name = models.CharField(max_length=255, help_text=help_text('rca.StandardIndexOurSites', 'site_name'))
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.StandardIndexOurSites', 'image'))

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('url'),
        FieldPanel('site_name')
    ]

class StandardIndexAd(Orderable):
    page = ParentalKey('rca.StandardIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.StandardIndexAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class StandardIndexCustomContentModules(Orderable):
    page = ParentalKey('rca.StandardIndex', related_name='custom_content_modules')
    custom_content_module = models.ForeignKey('rca.CustomContentModule', related_name='+', help_text=help_text('rca.StandardIndexCustomContentModules', 'custom_content_module'))

    panels = [
        SnippetChooserPanel('custom_content_module', CustomContentModule),
    ]

class StandardIndexContactSnippet(Orderable):
    page = ParentalKey('rca.StandardIndex', related_name='contact_snippets')
    contact_snippet = models.ForeignKey('rca.ContactSnippet', related_name='+', help_text=help_text('rca.StandardIndexContactSnippet', 'contact_snippet'))

    panels = [
        SnippetChooserPanel('contact_snippet', ContactSnippet),
    ]

class StandardIndex(Page, SocialFields, OptionalBlockFields, SidebarBehaviourFields):
    intro = RichTextField(help_text=help_text('rca.StandardIndex', 'intro'), blank=True)
    intro_link = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.StandardIndex', 'intro_link'))
    strapline = models.CharField(max_length=255, blank=True, help_text=help_text('rca.StandardIndex', 'strapline'))
    body = RichTextField(help_text=help_text('rca.StandardIndex', 'body'), blank=True)
    teasers_title = models.CharField(max_length=255, blank=True, help_text=help_text('rca.StandardIndex', 'teasers_title'))
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.StandardIndex', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.StandardIndex', 'background_image', default="The full bleed image in the background"))
    contact_title = models.CharField(max_length=255, blank=True, help_text=help_text('rca.StandardIndex', 'contact_title'))
    contact_address = models.TextField(blank=True, help_text=help_text('rca.StandardIndex', 'contact_address'))
    contact_link = models.URLField(blank=True, help_text=help_text('rca.StandardIndex', 'contact_link'))
    contact_link_text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.StandardIndex', 'contact_link_text'))
    news_carousel_area = models.CharField(max_length=255, choices=AREA_CHOICES, blank=True, help_text=help_text('rca.StandardIndex', 'news_carousel_area'))
    staff_feed_source = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True, help_text=help_text('rca.StandardIndex', 'staff_feed_source'))
    show_events_feed = models.BooleanField(default=False, help_text=help_text('rca.StandardIndex', 'show_events_feed'))
    events_feed_area = models.CharField(max_length=255, choices=EVENT_AREA_CHOICES, blank=True, help_text=help_text('rca.StandardIndex', 'events_feed_area'))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.StandardIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))
    hide_body = models.BooleanField(default=True, help_text=help_text('rca.StandardIndex', 'hide_body'))

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
        index.SearchField('strapline'),
        index.SearchField('body'),
    )

    search_name = None

    @property
    def staff_feed(self):
        # Get staff from manual feed
        manual_feed = self.manual_staff_feed.all()

        # Get from manual feed and append staff_role defined there
        feed2 = []
        for staffpage in manual_feed:
            staff = staffpage.staff
            staff.staff_role = staffpage.staff_role
            feed2.append(staff)

        manual_feed = feed2

        # Get from source feed and append first role title
        # for selected school of feed
        if self.staff_feed_source:
            feed_source = StaffPage.objects.filter(school=self.staff_feed_source).live()

            for staffpage in StaffPage.objects.filter(school=self.staff_feed_source):
                role = staffpage.roles.filter(school=self.staff_feed_source).first()

                if role:
                    staffpage.staff_role = role.title
        else:
            feed_source = StaffPage.objects.none()

        # Chain manual_feed + feed_source (any or both may be empty)
        feed = chain(manual_feed, feed_source)

        if manual_feed or self.staff_feed_source:
            return feed

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        # Get list of events
        events = EventItem.future_objects.filter(live=True).annotate(start_date=Min('dates_times__date_from')).filter(area=self.events_feed_area).order_by('start_date')

        # Event pagination
        page = request.GET.get('page')
        paginator = Paginator(events, 3)
        try:
            events = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            events = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            events = paginator.page(paginator.num_pages)

        # If the request is ajax, only return a new list of events
        # But if the pjax param is present we need to render the main template instead
        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, 'rca/includes/standard_index_events_listing.html', {
                'self': self,
                'events': events,
            })
        else:
            return render(request, self.template, {
                'self': self,
                'events': events,
            })


StandardIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('strapline', classname="full"),
    ImageChooserPanel('background_image'),
    MultiFieldPanel([
        FieldPanel('intro', classname="full"),
        PageChooserPanel('intro_link'),
    ],'Introduction'),
    FieldPanel('body', classname="full"),
    InlinePanel('carousel_items', label="Carousel content"),
    InlinePanel('manual_staff_feed', label="Manual staff feed"),
    FieldPanel('teasers_title'),
    InlinePanel('teasers', label="Teaser content"),
    InlinePanel('custom_content_modules', label="Modules"),
    InlinePanel('our_sites', label="Our sites"),
    InlinePanel('related_links', label="Related links"),
    InlinePanel('manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
    MultiFieldPanel([
        FieldPanel('contact_title'),
        FieldPanel('contact_address'),
        FieldPanel('contact_link'),
        FieldPanel('contact_link_text'),
    ],'Contact'),
    InlinePanel('contact_snippets', label="Contacts"),
    InlinePanel('contact_phone', label="Contact phone number"),
    InlinePanel('contact_email', label="Contact email address"),
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
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),

    MultiFieldPanel([
        FieldPanel('exclude_twitter_block'),
        FieldPanel('exclude_events_sidebar'),
        FieldPanel('exclude_global_adverts'),
        FieldPanel('hide_body'),
    ], 'Optional page elements'),
]

StandardIndex.settings_panels = [
    PublishingPanel(),
    MultiFieldPanel([
        FieldPanel('collapse_upcoming_events'),
    ], 'Sidebar behaviour'),
]


# == Home page ==

class HomePageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.HomePage', related_name='carousel_items')

class HomePageAd(Orderable):
    page = ParentalKey('rca.HomePage', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.HomePageAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class HomePageRelatedLink(Orderable, RelatedLinkMixin):
    page = ParentalKey('rca.HomePage', related_name='related_links')

class HomePage(Page, SocialFields):
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.HomePage', 'background_image', default="The full bleed image in the background"))
    news_item_1 = models.ForeignKey('wagtailcore.Page', null=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.HomePage', 'news_item_1'))
    news_item_2 = models.ForeignKey('wagtailcore.Page', null=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.HomePage', 'news_item_2'))
    packery_news = models.IntegerField("Number of news items to show", null=True, blank=True, choices=((0,0),(1,1),(2,2),(3,3),(4,4),(5,5),), help_text=help_text('rca.HomePage', 'packery_news'))
    packery_staff = models.IntegerField("Number of staff to show", null=True, blank=True, choices=((0,0),(1,1),(2,2),(3,3),(4,4),(5,5),), help_text=help_text('rca.HomePage', 'packery_staff'))
    packery_student_work = models.IntegerField("Number of student work items to show", null=True, blank=True, choices=((0,0),(1,1),(2,2),(3,3),(4,4),(5,5),), help_text=help_text('rca.HomePage', 'packery_student_work', default="Student pages flagged to Show On Homepage must have at least one carousel item"))
    packery_tweets = models.IntegerField("Number of tweets to show", null=True, blank=True, choices=((0,0),(1,1),(2,2),(3,3),(4,4),(5,5),), help_text=help_text('rca.HomePage', 'packery_tweets'))
    packery_rcanow = models.IntegerField("Number of RCA Now items to show", null=True, blank=True, choices=((0,0),(1,1),(2,2),(3,3),(4,4),(5,5),), help_text=help_text('rca.HomePage', 'packery_rcanow'))
    packery_research = models.IntegerField("Number of research items to show", null=True, blank=True, choices=((0,0),(1,1),(2,2),(3,3),(4,4),(5,5),), help_text=help_text('rca.HomePage', 'packery_research'))
    packery_alumni = models.IntegerField("Number of alumni to show", null=True, blank=True, choices=((0,0),(1,1),(2,2),(3,3),(4,4),(5,5),), help_text=help_text('rca.HomePage', 'packery_alumni'))
    packery_review = models.IntegerField("Number of reviews to show", null=True, blank=True, choices=((0,0),(1,1),(2,2),(3,3),(4,4),(5,5),), help_text=help_text('rca.HomePage', 'packery_review'))
    packery_events = models.IntegerField("Number of events to show (excluding RCA Talks)", null=True, blank=False, choices=((0,0),(1,1),(2,2),(3,3),(4,4),(5,5),), help_text=help_text('rca.HomePage', 'packery_events'))
    packery_events_rcatalks = models.IntegerField("Number of RCA Talk events to show", null=True, blank=False, choices=((0,0),(1,1),(2,2),(3,3),(4,4),(5,5),), help_text=help_text('rca.HomePage', 'packery_events_rcatalks'))
    packery_blog = models.IntegerField("Number of blog items to show", null=True, blank=False, choices=((0,0),(1,1),(2,2),(3,3),(4,4),(5,5),), help_text=help_text('rca.HomePage', 'packery_blog'))
    student_stories = models.IntegerField("Number of student stories to show", null=True, blank=False, choices=((0,0),(1,1),(2,2),(3,3),(4,4),(5,5),), help_text=help_text('rca.HomePage', 'student_stories'))
    alumni_stories = models.IntegerField("Number of student stories to show", null=True, blank=False, choices=((0,0),(1,1),(2,2),(3,3),(4,4),(5,5),), help_text=help_text('rca.HomePage', 'alumni_stories'))


    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.HomePage', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.HomePage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    def future_events(self):
        return EventItem.future_objects.filter(live=True, path__startswith=self.path)

    def past_events(self):
        return EventItem.past_objects.filter(live=True, path__startswith=self.path)

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        exclude = []

        if self.news_item_1:
            exclude.append(self.news_item_1.id)
        if self.news_item_2:
            exclude.append(self.news_item_2.id)

        if request.GET.get('exclude'):
            for extra_exclude in request.GET.get('exclude', '').split(','):
                try:
                    exclude.append(int(extra_exclude))
                except (TypeError, ValueError):
                    pass

        news = NewsItem.objects.filter(live=True, show_on_homepage=True).order_by('-date')
        staff = StaffPage.objects.filter(live=True, show_on_homepage=True).order_by('random_order')
        student = NewStudentPage.objects.filter(live=True, show_on_homepage=True).order_by('random_order')
        rcanow = RcaNowPage.objects.filter(live=True, show_on_homepage=True).order_by('?')
        research = ResearchItem.objects.filter(live=True, show_on_homepage=True).order_by('random_order')
        alumni = AlumniPage.objects.filter(live=True, show_on_homepage=True).order_by('random_order')
        review = ReviewPage.objects.filter(live=True, show_on_homepage=True).order_by('?')
        events = EventItem.future_objects.filter(live=True, show_on_homepage=True).exclude(audience='rcatalks').order_by('?')
        events_rcatalks = EventItem.future_objects.filter(live=True, show_on_homepage=True, audience='rcatalks').order_by('?')
        blog = RcaBlogPage.objects.filter(live=True, show_on_homepage=True).order_by('-date')
        student_stories = StandardPage.objects.filter(show_on_homepage=True, tags__name__iexact=StandardPage.STUDENT_STORY_TAG)\
            .exclude(tags__name__iexact=StandardPage.ALUMNI_STORY_TAG).order_by('?')
        alumni_stories = StandardPage.objects.filter(show_on_homepage=True, tags__name__iexact=StandardPage.ALUMNI_STORY_TAG).order_by('?')
        tweets = [[], [], [], [], []]

        if exclude:
            news = news.exclude(id__in=exclude)
            staff = staff.exclude(id__in=exclude)
            student = student.exclude(id__in=exclude)
            news = news.exclude(id__in=exclude)
            rcanow = rcanow.exclude(id__in=exclude)
            research = research.exclude(id__in=exclude)
            alumni = alumni.exclude(id__in=exclude)
            review = review.exclude(id__in=exclude)
            events = events.exclude(id__in=exclude)
            events_rcatalks = events_rcatalks.exclude(id__in=exclude)
            blog = blog.exclude(id__in=exclude)
            student_stories = student_stories.exclude(id__in=exclude)
            alumni_stories = alumni_stories.exclude(id__in=exclude)

        packery = list(chain(
            news[:self.packery_news],
            staff[:self.packery_staff],
            student[:self.packery_student_work],
            rcanow[:self.packery_rcanow],
            research[:self.packery_research],
            alumni[:self.packery_alumni],
            review[:self.packery_review],
            events[:self.packery_events],
            events_rcatalks[:self.packery_events_rcatalks],
            blog[:self.packery_blog],
            student_stories[:self.student_stories],
            alumni_stories[:self.alumni_stories],
        ))

        # only add tweets to the packery content if not using the plus button
        if not exclude:
            packery = packery + tweets[:self.packery_tweets]

        random.shuffle(packery)

        # programme = request.GET.get('programme')
        # school = request.GET.get('school')
        # location = request.GET.get('location')
        # location_other = request.GET.get('location_other')
        # area = request.GET.get('area')
        # audience = request.GET.get('audience')
        # period = request.GET.get('period')

        # if period == 'past':
        #     events = self.past_events()
        # else:
        #     events = self.future_events()

        # if programme and programme != '':
             # events = events.filter(related_programmes__programme__in=get_programme_synonyms(programme))
        # if school and school != 'all':
        #     events = events.filter(related_schools__school=school)
        # if location and location != '':
        #     events = events.filter(location=location)
        # if area and area != 'all':
        #     events = events.filter(related_areas__area=area)
        # if audience and audience != '':
        #     events = events.filter(audience=audience)
        # events = events.annotate(start_date=Min('dates_times__date_from')).order_by('start_date')

        # related_programmes = SCHOOL_PROGRAMME_MAP[str(date.today().year)].get(school, []) if school else []

        # page = request.GET.get('page')
        # paginator = Paginator(events, 10)  # Show 10 events per page
        # try:
        #     events = paginator.page(page)
        # except PageNotAnInteger:
        #     # If page is not an integer, deliver first page.
        #     events = paginator.page(1)
        # except EmptyPage:
        #     # If page is out of range (e.g. 9999), deliver last page of results.
        #     events = paginator.page(paginator.num_pages)

        if request.is_ajax():
            return render(request, "rca/includes/homepage_packery.html", {
                'self': self,
                'packery': packery
            })
        else:
            return render(request, self.template, {
                'self': self,
                'packery': packery
            })

HomePage.content_panels = [
    FieldPanel('title', classname="full title"),
    ImageChooserPanel('background_image'),
    InlinePanel('carousel_items', label="Carousel content"),
    PageChooserPanel('news_item_1'),
    PageChooserPanel('news_item_2'),
    MultiFieldPanel([
        FieldPanel('packery_news'),
        FieldPanel('packery_staff'),
        FieldPanel('packery_student_work'),
        FieldPanel('packery_tweets'),
        FieldPanel('twitter_feed'),
        FieldPanel('packery_rcanow'),
        FieldPanel('packery_research'),
        FieldPanel('packery_alumni'),
        FieldPanel('packery_review'),
        FieldPanel('packery_events'),
        FieldPanel('packery_events_rcatalks'),
        FieldPanel('packery_blog'),
        FieldPanel('student_stories'),
        FieldPanel('alumni_stories'),
    ], 'Packery content'),
    InlinePanel('related_links', label="Related links"),
    InlinePanel('manual_adverts', label="Manual adverts"),
]

HomePage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]


# == Job page ==

class JobPageReusableTextSnippet(Orderable):
    page = ParentalKey('rca.JobPage', related_name='reusable_text_snippets')
    reusable_text_snippet = models.ForeignKey('rca.ReusableTextSnippet', related_name='+', help_text=help_text('rca.JobPageReusableTextSnippet', 'reusable_text_snippet'))

    panels = [
        SnippetChooserPanel('reusable_text_snippet', ReusableTextSnippet),
    ]

class JobPage(Page, SocialFields):
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, null=True, blank=True, help_text=help_text('rca.JobPage', 'programme'))
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, null=True, blank=True, help_text=help_text('rca.JobPage', 'school'))
    other_department = models.CharField(max_length=255, blank=True, help_text=help_text('rca.JobPage', 'other_department'))
    closing_date = models.DateField(help_text=help_text('rca.JobPage', 'closing_date'))
    interview_date = models.DateField(null=True, blank=True, help_text=help_text('rca.JobPage', 'interview_date'))
    responsible_to = models.CharField(max_length=255, blank=True, help_text=help_text('rca.JobPage', 'responsible_to'))
    required_hours = models.CharField(max_length=255, blank=True, help_text=help_text('rca.JobPage', 'required_hours'))
    campus = models.CharField(max_length=255, choices=CAMPUS_CHOICES, null=True, blank=True, help_text=help_text('rca.JobPage', 'campus'))
    salary = models.CharField(max_length=255, blank=True, help_text=help_text('rca.JobPage', 'salary'))
    ref_number = models.CharField(max_length=255, blank=True, help_text=help_text('rca.JobPage', 'ref_number'))
    grade = models.CharField(max_length=255, blank=True, help_text=help_text('rca.JobPage', 'grade'))
    description = RichTextField(help_text=help_text('rca.JobPage', 'description'))
    download_info = models.ForeignKey('wagtaildocs.Document', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.JobPage', 'download_info'))
    listing_intro = models.CharField(max_length=255, blank=True, help_text=help_text('rca.JobPage', 'listing_intro', default="Used only on pages listing jobs"))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.JobPage', 'show_on_homepage'))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.JobPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('get_programme_display'),
        index.SearchField('get_school_display'),
        index.SearchField('other_department'),
        index.SearchField('get_campus_display'),
        index.SearchField('description'),
    )

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
    InlinePanel('reusable_text_snippets', label="Application and equal opportunities monitoring form text"),
]

JobPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_on_homepage'),
        FieldPanel('listing_intro'),
        ImageChooserPanel('feed_image'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]


# == Jobs index page ==

class JobsIndexRelatedLink(Orderable, RelatedLinkMixin):
    page = ParentalKey('rca.JobsIndex', related_name='related_links')

class JobsIndexAd(Orderable):
    page = ParentalKey('rca.JobsIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.JobsIndexAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class JobsIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.JobsIndex', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.JobsIndex', 'body'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.JobsIndex', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.JobsIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
        index.SearchField('body'),
    )

    search_name = None

JobsIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    InlinePanel('related_links', label="Related links"),
    InlinePanel('manual_adverts', label="Manual adverts"),
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
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]



# == Alumni index page ==

class AlumniIndexRelatedLink(Orderable, RelatedLinkMixin):
    page = ParentalKey('rca.AlumniIndex', related_name='related_links')

class AlumniIndexAd(Orderable):
    page = ParentalKey('rca.AlumniIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.AlumniIndexAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class AlumniIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.AlumniIndex', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.AlumniIndex', 'body'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.AlumniIndex', 'twitter_feed'))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.AlumniIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
        index.SearchField('body'),
    )

    search_name = None

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        school = request.GET.get('school')
        programme = request.GET.get('programme')

        alumni_pages = AlumniPage.objects.filter(live=True)

        # Run school and programme filters
        alumni_pages, filters = run_filters(alumni_pages, [
            ('school', 'school', school),
            ('programme', 'programme', programme),
        ])

        alumni_pages = alumni_pages.order_by('random_order')

        page = request.GET.get('page')
        paginator = Paginator(alumni_pages, 11)
        try:
            alumni_pages = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            alumni_pages = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            alumni_pages = paginator.page(paginator.num_pages)

        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, "rca/includes/alumni_pages_listing.html", {
                'self': self,
                'alumni_pages': alumni_pages,
                'filters': json.dumps(filters),
            })
        else:
            return render(request, self.template, {
                'self': self,
                'alumni_pages': alumni_pages,
                'filters': json.dumps(filters),
            })


AlumniIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    InlinePanel('related_links', label="Related links"),
    InlinePanel('manual_adverts', label="Manual adverts"),
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
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]


# == Alumni profile page ==

class AlumniPage(Page, SocialFields):
    profile_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.AlumniPage', 'profile_image'))
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, help_text=help_text('rca.AlumniPage', 'school'))
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, help_text=help_text('rca.AlumniPage', 'programme'))
    year = models.CharField(max_length=4, blank=True, help_text=help_text('rca.AlumniPage', 'year'))
    intro = RichTextField(help_text=help_text('rca.AlumniPage', 'intro'), blank=True)
    listing_intro = models.CharField(max_length=100, blank=True, help_text=help_text('rca.AlumniPage', 'listing_intro', default="Used only on pages displaying a list of pages of this type"))
    biography = RichTextField(help_text=help_text('rca.AlumniPage', 'biography'))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.AlumniPage', 'show_on_homepage'))
    random_order = models.IntegerField(null=True, blank=True, editable=False)
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.AlumniPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('get_school_display'),
        index.SearchField('get_programme_display'),
        index.SearchField('intro'),
        index.SearchField('biography'),
    )

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
        FieldPanel('search_description'),
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
    title = models.CharField(max_length=255, help_text=help_text('rca.StaffPageRole', 'title'))
    school = models.CharField(max_length=255, blank=True, choices=SCHOOL_CHOICES, help_text=help_text('rca.StaffPageRole', 'school'))
    programme = models.CharField(max_length=255, blank=True, choices=PROGRAMME_CHOICES, help_text=help_text('rca.StaffPageRole', 'programme'))
    area = models.CharField(max_length=255, blank=True, choices=STAFF_AREA_CHOICES, help_text=help_text('rca.StaffPageRole', 'area'))
    email = models.EmailField(max_length=255, blank=True, help_text=help_text('rca.StaffPageRole', 'email'))

    panels = [
        FieldPanel('title'),
        FieldPanel('school'),
        FieldPanel('programme'),
        FieldPanel('area'),
        FieldPanel('email'),
    ]

class StaffPageCollaborations(Orderable):
    page = ParentalKey('rca.StaffPage', related_name='collaborations')
    title = models.CharField(max_length=255, help_text=help_text('rca.StaffPageCollaborations', 'title'))
    link = models.URLField(help_text=help_text('rca.StaffPageCollaborations', 'link'))
    text = RichTextField(help_text=help_text('rca.StaffPageCollaborations', 'text'))
    date = models.CharField(max_length=255, blank=True, help_text=help_text('rca.StaffPageCollaborations', 'date'))

    panels = [
        FieldPanel('title'),
        FieldPanel('link'),
        FieldPanel('text'),
        FieldPanel('date'),
    ]

class StaffPagePublicationExhibition(Orderable):
    page = ParentalKey('rca.StaffPage', related_name='publications_exhibitions')
    title = models.CharField(max_length=255, help_text=help_text('rca.StaffPagePublicationExhibition', 'title'))
    typeof = models.CharField("Type", max_length=255, choices=[('publication', 'Publication'),('exhibition', 'Exhibition')], help_text=help_text('rca.StaffPagePublicationExhibition', 'typeof'))
    location_year = models.CharField("Location and year", max_length=255, help_text=help_text('rca.StaffPagePublicationExhibition', 'location_year'))
    authors_collaborators = models.TextField("Authors/collaborators", blank=True, help_text=help_text('rca.StaffPagePublicationExhibition', 'authors_collaborators'))
    link = models.URLField(blank=True, help_text=help_text('rca.StaffPagePublicationExhibition', 'link'))
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.StaffPagePublicationExhibition', 'image'))
    rca_content_id = models.CharField(max_length=255, blank=True, editable=False) # for import

    panels = [
        FieldPanel('title'),
        FieldPanel('typeof'),
        FieldPanel('location_year'),
        FieldPanel('authors_collaborators'),
        FieldPanel('link'),
        ImageChooserPanel('image'),
    ]

class StaffPage(Page, SocialFields):
    school = models.CharField(max_length=255, blank=True, choices=AREA_CHOICES, help_text=help_text('rca.StaffPage', 'school', default="Please complete this field for academic and administrative staff only"))
    profile_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.StaffPage', 'profile_image'))
    staff_type = models.CharField(max_length=255, blank=True, choices=STAFF_TYPES_CHOICES, help_text=help_text('rca.StaffPage', 'staff_type'))
    staff_location = models.CharField(max_length=255, blank=True, choices=STAFF_LOCATION_CHOICES, help_text=help_text('rca.StaffPage', 'staff_location', default="Please complete this field for technical staff only"))
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.StaffPage', 'twitter_feed'))
    intro = RichTextField(help_text=help_text('rca.StaffPage', 'intro'), blank=True)
    biography = RichTextField(help_text=help_text('rca.StaffPage', 'biography'), blank=True)
    practice = RichTextField(help_text=help_text('rca.StaffPage', 'practice'), blank=True)
    publications_exhibtions_and_other_outcomes_placeholder = RichTextField(help_text=help_text('rca.StaffPage', 'publications_exhibtions_and_other_outcomes_placeholder'), blank=True)
    external_collaborations_placeholder = RichTextField(help_text=help_text('rca.StaffPage', 'external_collaborations_placeholder'), blank=True)
    current_recent_research = RichTextField(help_text=help_text('rca.StaffPage', 'current_recent_research'), blank=True)
    awards_and_grants = RichTextField(help_text=help_text('rca.StaffPage', 'awards_and_grants'), blank=True)
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.StaffPage', 'show_on_homepage'))
    show_on_programme_page = models.BooleanField(default=False, help_text=help_text('rca.StaffPage', 'show_on_programme_page'))
    listing_intro = models.CharField(max_length=100, blank=True, help_text=help_text('rca.StaffPage', 'listing_intro', default="Used only on pages displaying a list of pages of this type"))
    research_interests = RichTextField(help_text=help_text('rca.StaffPage', 'research_interests'), blank=True)
    title_prefix = models.CharField(max_length=255, blank=True, help_text=help_text('rca.StaffPage', 'title_prefix'))
    first_name = models.CharField(max_length=255, help_text=help_text('rca.StaffPage', 'first_name'))
    last_name = models.CharField(max_length=255, help_text=help_text('rca.StaffPage', 'last_name'))
    supervised_student_other = models.CharField(max_length=255, blank=True, help_text=help_text('rca.StaffPage', 'supervised_student_other', default="Enter names of research students here who don\'t have a student profile. Supervised students with profile pages are pulled in automatically."))
    rca_content_id = models.CharField(max_length=255, blank=True, editable=False) # for import
    random_order = models.IntegerField(null=True, blank=True, editable=False)
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.StaffPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('get_school_display'),
        index.SearchField('get_staff_type_display'),
        index.SearchField('intro'),
        index.SearchField('biography'),
    )

    search_name = 'Staff'

    @property
    def programmes(self):
        return list({role.programme for role in StaffPageRole.objects.filter(page=self) if role.programme})

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
    FieldPanel('staff_location'),
    InlinePanel('roles', label="Roles"),
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

    InlinePanel('carousel_items', label="Selected Work Carousel Content"),
    InlinePanel('collaborations', label="Collaborations"),
    InlinePanel('publications_exhibitions', label="Publications and Exhibitions"),
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
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]

# == Staff index page ==

class StaffIndexAd(Orderable):
    page = ParentalKey('rca.StaffIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.StaffIndexAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class StaffIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.StaffIndex', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.StaffIndex', 'body'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.StaffIndex', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.StaffIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    indexed = False

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        staff_type = request.GET.get('staff_type')
        school = request.GET.get('school')
        programme = request.GET.get('programme')
        area = request.GET.get('area')

        staff_pages = StaffPage.objects.filter(live=True)

        # Run filters
        staff_pages, filters = run_filters(staff_pages, [
            ('school', 'roles__school', school),
            ('programme', 'roles__programme', programme),
            ('staff_type', 'staff_type', staff_type),
            ('area', 'roles__area', area),
        ])

        # Remove duplicates (#615)
        staff_pages = staff_pages.distinct()

        staff_pages = staff_pages.order_by('-random_order')

        # research_items.order_by('-year')

        page = request.GET.get('page')
        paginator = Paginator(staff_pages, 17)
        try:
            staff_pages = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            staff_pages = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            staff_pages = paginator.page(paginator.num_pages)

        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, "rca/includes/staff_pages_listing.html", {
                'self': self,
                'staff_pages': staff_pages,
                'filters': json.dumps(filters),
            })
        else:
            return render(request, self.template, {
                'self': self,
                'staff_pages': staff_pages,
                'filters': json.dumps(filters),
            })

StaffIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    InlinePanel('manual_adverts', label="Manual adverts"),
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
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]

# == Research student index ==

class ResearchStudentIndexAd(Orderable):
    page = ParentalKey('rca.ResearchStudentIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.ResearchStudentIndexAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class ResearchStudentIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.ResearchStudentIndex', 'intro'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ResearchStudentIndex', 'twitter_feed', default="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term"))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ResearchStudentIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
    )

    search_name = None

    def current_students_q(self):
        current_year = timezone.now().year
        return (~models.Q(phd_school='') & (models.Q(phd_graduation_year='') | models.Q(phd_graduation_year__gte=current_year))) | (~models.Q(mphil_school='') & (models.Q(mphil_graduation_year='') | models.Q(mphil_graduation_year__gte=current_year)))

    def phd_students_q(self, period=None):
        q = ~models.Q(phd_school='')

        if period == 'current':
            q &= self.current_students_q()
        elif period == 'past':
            q &= ~self.current_students_q()

        return q

    def mphil_students_q(self, period=None):
        q = ~models.Q(mphil_school='')

        if period == 'current':
            q &= self.current_students_q()
        elif period == 'past':
            q &= ~self.current_students_q()

        return q

    def get_students_q(self, school=None, programme=None, period=None):
        # Get students
        phd_students_q = self.phd_students_q(period)
        mphil_students_q = self.mphil_students_q(period)

        # Run filters
        phd_filters = run_filters_q(NewStudentPage, phd_students_q, [
            ('school', 'phd_school', school),
            ('programme', 'phd_programme', programme),
        ])
        mphil_filters = run_filters_q(NewStudentPage, mphil_students_q, [
            ('school', 'mphil_school', school),
            ('programme', 'mphil_programme', programme),
        ])

        # Combine filters
        filters = combine_filters(phd_filters, mphil_filters)

        # Add combined filters to both groups
        phd_students_q &= get_filters_q(filters, {
            'school': 'phd_school',
            'programme': 'phd_programme',
        })
        mphil_students_q &= get_filters_q(filters, {
            'school': 'mphil_school',
            'programme': 'mphil_programme',
        })

        return phd_students_q, mphil_students_q, filters

    def all_students(self):
        phd_students_q, mphil_students_q, filters = self.get_students_q()
        return NewStudentPage.objects.filter(live=True).filter(phd_students_q | mphil_students_q)

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        school = request.GET.get('school')
        programme = request.GET.get('programme')
        period = request.GET.get('period')

        # Get students
        phd_students_q, mphil_students_q, filters = self.get_students_q(school, programme, period)
        research_students = NewStudentPage.objects.filter(live=True).filter(phd_students_q | mphil_students_q)

        research_students = research_students.distinct().order_by('random_order')

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

        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, "rca/includes/research_students_pages_listing.html", {
                'self': self,
                'research_students': research_students,
                'filters': json.dumps(filters),
            })
        else:
            return render(request, self.template, {
                'self': self,
                'research_students': research_students,
                'filters': json.dumps(filters),
            })

    def route(self, request, path_components):
        # If there are any path components, try checking if one if them is a student in the research student index
        # If so, re route through the student page
        if len(path_components) == 1:
            try:
                student_page = self.all_students().get(slug=path_components[0])
                return RouteResult(student_page.specific, kwargs={'view': 'research'})
            except NewStudentPage.DoesNotExist:
                pass

        return super(ResearchStudentIndex, self).route(request, path_components)

ResearchStudentIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel('manual_adverts', label="Manual adverts"),
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
        FieldPanel('search_description'),
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

class StudentPagePublication(Orderable):
    page = ParentalKey('rca.StudentPage', related_name='publications')
    name = models.CharField(max_length=255, blank=True)

    panels = [FieldPanel('name')]

class StudentPageConference(Orderable):
    page = ParentalKey('rca.StudentPage', related_name='conferences')
    name = models.CharField(max_length=255, blank=True)

    panels = [FieldPanel('name')]

class StudentPageSupervisor(Orderable):
    page = ParentalKey('rca.StudentPage', related_name='supervisors')
    supervisor = models.ForeignKey('rca.StaffPage', related_name='+', null=True, blank=True)
    supervisor_other = models.CharField(max_length=255, blank=True)

    panels = [
        PageChooserPanel('supervisor'),
        FieldPanel('supervisor_other'),
    ]

class StudentPage(Page, SocialFields):
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES)
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES)
    degree_qualification = models.CharField(max_length=255, choices=QUALIFICATION_CHOICES)
    degree_subject = models.CharField(max_length=255, choices=SUBJECT_CHOICES)
    degree_year = models.CharField(max_length=4, blank=True)
    graduation_year = models.CharField(max_length=4, blank=True, help_text="This field should only be filled in for students whose courses are more than 1 year. Should be filled in after graduation.")
    specialism = models.CharField(max_length=255, blank=True)
    profile_image = models.ForeignKey('rca.RcaImage', on_delete=models.SET_NULL, related_name='+', null=True, blank=True)
    statement = RichTextField(blank=True)
    work_description = RichTextField(blank=True)
    work_type = models.CharField(max_length=255, choices=WORK_TYPES_CHOICES, blank=True)
    work_location = models.CharField(max_length=255, choices=CAMPUS_CHOICES, blank=True)
    work_awards = models.CharField(max_length=255, blank=True, verbose_name='Show RCA work awards')
    funding = models.CharField(max_length=255, blank=True)
    student_twitter_feed = models.CharField(max_length=255, blank=True, help_text="Enter Twitter handle without @ symbol.")
    twitter_feed = models.CharField(max_length=255, blank=True)
    rca_content_id = models.CharField(max_length=255, blank=True, editable=False)  # for import
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    show_on_homepage = models.BooleanField(default=False)
    random_order = models.IntegerField(null=True, blank=True, editable=False)
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio.")

    search_fields = Page.search_fields + (
        index.SearchField('get_school_display'),
        index.SearchField('get_programme_display'),
        index.SearchField('statement'),
    )

    @property
    def is_researchstudent(self):
        return self.get_parent().content_type.model_class() == ResearchStudentIndex

    @property
    def search_name(self):
        if self.degree_qualification == 'innovationrca-fellow':
            return 'InnovationRCA Fellow'

        if self.is_researchstudent:
            return 'Research Student'
        else:
            return self.get_degree_qualification_display() + " Graduate"

    @property
    def work_tab_title(self):
        if self.is_researchstudent:
            return "Research Work"
        elif self.get_parent().content_type.model_class() == RcaNowIndex:
            return "RCA Now"
        else:
            return "Show RCA Work"

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
    FieldPanel('graduation_year'),
    ImageChooserPanel('profile_image'),
    InlinePanel('supervisors', label="Supervisor"),
    InlinePanel('email', label="Email"),
    InlinePanel('phone', label="Phone"),
    InlinePanel('website', label="Website"),
    FieldPanel('student_twitter_feed'),
    FieldPanel('twitter_feed'),
    InlinePanel('degrees', label="Previous degrees"),
    InlinePanel('exhibitions', label="Exhibition"),
    InlinePanel('experiences', label="Experience"),
    InlinePanel('publications', label="Publications"),
    InlinePanel('conferences', label="Conferences"),
    FieldPanel('funding'),
    InlinePanel('awards', label="Awards"),
    FieldPanel('statement', classname="full"),
    InlinePanel('carousel_items', label="Carousel content"),
    MultiFieldPanel([
        FieldPanel('work_description', classname="full"),
        FieldPanel('work_type'),
        FieldPanel('work_location'),
    ], 'Show RCA work'),
    InlinePanel('collaborators', label="Show RCA work collaborator"),
    InlinePanel('sponsor', label="Show RCA work sponsor"),
    FieldPanel('work_awards'),
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
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]

# When a user logs in, check for any StudentPages that have no owner but have an email address
# matching this user, and reassign them to be owned by this user
@receiver(user_logged_in)
def reassign_student_pages(sender, request, user, **kwargs):
    StudentPage.objects.filter(owner__isnull=True, email__email__iexact=user.email).update(owner=user)


# == New Student page ==

class CarouselItemManager(models.Manager):
    use_for_related_fields = True

    def no_videos(self):
        return self.all().filter(embedly_url='')


# General
class NewStudentPagePreviousDegree(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='previous_degrees')
    degree = models.CharField(max_length=255, help_text=help_text('rca.NewStudentPagePreviousDegree', 'degree', default="Please include the degree level, subject, institution name and year of graduation, separated by commas"))

    panels = [FieldPanel('degree')]

class NewStudentPageExhibition(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='exhibitions')
    exhibition = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageExhibition', 'exhibition', default="Please include exhibition title, gallery, city and year, separated by commas"))

    panels = [FieldPanel('exhibition')]

class NewStudentPageExperience(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='experiences')
    experience = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageExperience', 'experience', default="Please include job title, company name, city and year(s), separated by commas"))

    panels = [FieldPanel('experience')]

class NewStudentPageContactsEmail(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='emails')
    email = models.EmailField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageContactsEmail', 'email', default="Students can use personal email as well as firstname.surname@network.rca.ac.uk"))

    panels = [FieldPanel('email')]

class NewStudentPageContactsPhone(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='phones')
    phone = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageContactsPhone', 'phone', default="UK mobile e.g. 07XXX XXXXXX or overseas landline, e.g. +33 (1) XXXXXXX"))

    panels = [FieldPanel('phone')]

class NewStudentPageContactsWebsite(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='websites')
    website = models.URLField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageContactsWebsite', 'website'))

    panels = [FieldPanel('website')]

class NewStudentPagePublication(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='publications')
    name = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPagePublication', 'name', default="Please include author (if not you), title of article, title of publication, issue number, year, pages, separated by commas"))

    panels = [FieldPanel('name')]

class NewStudentPageConference(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='conferences')
    name = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageConference', 'name', default="Please include paper, title of conference, institution, date, separated by commas"))

    panels = [FieldPanel('name')]

class NewStudentPageAward(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='awards')
    award = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageAward', 'award', default="Please include prize, award title and year, separated by commas"))

    panels = [FieldPanel('award')]


# Show
class NewStudentPageShowCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.NewStudentPage', related_name='show_carousel_items')

    objects = CarouselItemManager()

class NewStudentPageShowCollaborator(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='show_collaborators')
    name = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageShowCollaborator', 'name', default="Please include collaborator's name and programme (if RCA), separated by commas"))

    panels = [FieldPanel('name')]

class NewStudentPageShowSponsor(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='show_sponsors')
    name = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageShowSponsor', 'name', default="Please list companies and individuals that have provided financial or in kind sponsorship for your final project, separated by commas"))

    panels = [FieldPanel('name')]


# MPhil
class NewStudentPageMPhilCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.NewStudentPage', related_name='mphil_carousel_items')

    objects = CarouselItemManager()

class NewStudentPageMPhilCollaborator(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='mphil_collaborators')
    name = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageMPhilCollaborator', 'name', default="Please include collaborator's name and programme (if RCA), separated by commas"))

    panels = [FieldPanel('name')]

class NewStudentPageMPhilSponsor(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='mphil_sponsors')
    name = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageMPhilSponsor', 'name', default="Please list companies and individuals that have provided financial or in kind sponsorship for your final project, separated by commas"))

    panels = [FieldPanel('name')]

class NewStudentPageMPhilSupervisor(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='mphil_supervisors')
    supervisor = models.ForeignKey('rca.StaffPage', related_name='+', null=True, blank=True, help_text=help_text('rca.NewStudentPageMPhilSupervisor', 'supervisor', default="Please select your RCA supervisor's profile page or enter the name of an external supervisor"))
    supervisor_other = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageMPhilSupervisor', 'supervisor_other'))

    @property
    def name(self):
        if self.supervisor:
            return self.supervisor.title
        else:
            return self.supervisor_other

    @property
    def link(self):
        if self.supervisor:
            return self.supervisor.url

    panels = [
        PageChooserPanel('supervisor'),
        FieldPanel('supervisor_other'),
    ]


# PhD
class NewStudentPagePhDCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.NewStudentPage', related_name='phd_carousel_items')

    objects = CarouselItemManager()

class NewStudentPagePhDCollaborator(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='phd_collaborators')
    name = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPagePhDCollaborator', 'name', default="Please include collaborator's name and programme (if RCA), separated by commas"))

    panels = [FieldPanel('name')]

class NewStudentPagePhDSponsor(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='phd_sponsors')
    name = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPagePhDSponsor', 'name', default="Please list companies and individuals that have provided financial or in kind sponsorship for your final project, separated by commas"))

    panels = [FieldPanel('name')]

class NewStudentPagePhDSupervisor(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='phd_supervisors')
    supervisor = models.ForeignKey('rca.StaffPage', related_name='+', null=True, blank=True, help_text=help_text('rca.NewStudentPagePhDSupervisor', 'supervisor', default="Please select your RCA supervisor's profile page or enter the name of an external supervisor"))
    supervisor_other = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPagePhDSupervisor', 'supervisor_other'))

    @property
    def name(self):
        if self.supervisor:
            return self.supervisor.title
        else:
            return self.supervisor_other

    @property
    def link(self):
        if self.supervisor:
            return self.supervisor.url

    panels = [
        PageChooserPanel('supervisor'),
        FieldPanel('supervisor_other'),
    ]

class NewStudentPage(Page, SocialFields):
    # General details
    first_name = models.CharField(max_length=255, help_text=help_text('rca.NewStudentPage', 'first_name'))
    last_name = models.CharField(max_length=255, help_text=help_text('rca.NewStudentPage', 'last_name'))
    profile_image = models.ForeignKey('rca.RcaImage', on_delete=models.SET_NULL, related_name='+', null=True, blank=True, help_text=help_text('rca.NewStudentPage', 'profile_image', default="Self-portrait image, 500x500px"))
    statement = RichTextField(help_text=help_text('rca.NewStudentPage', 'statement'), blank=True)
    twitter_handle = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPage', 'twitter_handle', default="Please enter Twitter handle without the @ symbol"))
    funding = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPage', 'funding', default="Please include major funding bodies, including research councils"))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.NewStudentPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.NewStudentPage', 'show_on_homepage'))
    innovation_rca_fellow = models.BooleanField(default=False, help_text=help_text('rca.NewStudentPage', 'innovation_rca_fellow', default="Please tick this box only if you are currently an InnovationRCA Fellow"))
    postcard_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.NewStudentPage', 'postcard_image', default="Please upload images sized to A6 plus 2mm 'bleed' (152 x 109mm or 1795 x 1287px @ 300 dpi) - this must be uploaded at the correct size for printed postcards"))

    # Hidden fields
    rca_content_id = models.CharField(max_length=255, blank=True, editable=False)  # for import
    random_order = models.IntegerField(null=True, blank=True, editable=False)

    # MA details
    ma_school = models.CharField("School", max_length=255, choices=SCHOOL_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'ma_school'))
    ma_programme = models.CharField("Programme", max_length=255, choices=PROGRAMME_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'ma_programme'))
    ma_graduation_year = models.CharField("Graduation year",max_length=4, blank=True, help_text=help_text('rca.NewStudentPage', 'ma_graduation_year'))
    ma_specialism = models.CharField("Specialism", max_length=255, choices=SPECIALISM_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'ma_specialism'))
    ma_in_show = models.BooleanField("In show", default=False, help_text=help_text('rca.NewStudentPage', 'ma_in_show', default="Please tick only if you're in the Show this academic year"))
    show_work_title = models.CharField("Dissertation/project title", max_length=255, blank=True, help_text=help_text('rca.NewStudentPage', 'show_work_title'))
    show_work_type = models.CharField("Work type", max_length=255, choices=SHOW_WORK_TYPE_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'show_work_type'))
    show_work_location = models.CharField("Work location", max_length=255, choices=CAMPUS_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'show_work_location'))
    show_work_description = RichTextField(help_text=help_text('rca.NewStudentPage', 'show_work_description'), blank=True)

    # MPhil details
    mphil_school = models.CharField("School", max_length=255, choices=SCHOOL_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'mphil_school'))
    mphil_programme = models.CharField("Programme", max_length=255, choices=PROGRAMME_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'mphil_programme'))
    mphil_start_year = models.CharField("Start year", max_length=4, blank=True, help_text=help_text('rca.NewStudentPage', 'mphil_start_year'))
    mphil_graduation_year = models.CharField("Graduation year", max_length=4, blank=True, help_text=help_text('rca.NewStudentPage', 'mphil_graduation_year'))
    mphil_work_location = models.CharField("Work location", max_length=255, choices=CAMPUS_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'mphil_work_location'))
    mphil_dissertation_title = models.CharField("Dissertation title", max_length=255, blank=True, help_text=help_text('rca.NewStudentPage', 'mphil_dissertation_title'))
    mphil_statement = RichTextField(help_text=help_text('rca.NewStudentPage', 'mphil_statement'), blank=True)
    mphil_in_show = models.BooleanField("In show", default=False, help_text=help_text('rca.NewStudentPage', 'mphil_in_show', default="Please tick only if you're in the Show this academic year"))
    mphil_status = models.CharField("Status", max_length=255, choices=STATUS_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'mphil_status', default=''))
    mphil_degree_type = models.CharField("Degree type", max_length=255, choices=DEGREE_TYPE_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'mphil_degree_type'))

    # PhD details
    phd_school = models.CharField("School", max_length=255, choices=SCHOOL_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'phd_school'))
    phd_programme = models.CharField("Programme", max_length=255, choices=PROGRAMME_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'phd_programme'))
    phd_start_year = models.CharField("Start year", max_length=4, blank=True, help_text=help_text('rca.NewStudentPage', 'phd_start_year'))
    phd_graduation_year = models.CharField("Graduation year", max_length=4, blank=True, help_text=help_text('rca.NewStudentPage', 'phd_graduation_year'))
    phd_work_location = models.CharField("Work location", max_length=255, choices=CAMPUS_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'phd_work_location'))
    phd_dissertation_title = models.CharField("Dissertation title", max_length=255, blank=True, help_text=help_text('rca.NewStudentPage', 'phd_dissertation_title'))
    phd_statement = RichTextField(help_text=help_text('rca.NewStudentPage', 'phd_statement'), blank=True)
    phd_in_show = models.BooleanField("In show", default=False, help_text=help_text('rca.NewStudentPage', 'phd_in_show', default="Please tick only if you're in the Show this academic year"))
    phd_status = models.CharField("Status", max_length=255, choices=STATUS_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'phd_status', default=''))
    phd_degree_type = models.CharField("Degree type", max_length=255, choices=DEGREE_TYPE_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'phd_degree_type'))

    search_fields = Page.search_fields + (
        index.SearchField('first_name', partial_match=True, boost=50),
        index.SearchField('last_name', partial_match=True, boost=50),
        index.SearchField('statement'),

        index.SearchField('get_ma_school_display'),
        index.SearchField('get_ma_programme_display'),
        index.SearchField('ma_graduation_year'),
        index.SearchField('get_ma_specialism_display'),

        index.SearchField('show_work_title'),
        index.SearchField('get_show_work_type_display'),
        index.SearchField('get_show_work_location_display'),
        index.SearchField('show_work_description'),
        index.FilterField('ma_in_show'),
        index.FilterField('ma_school'),
        index.FilterField('ma_programme'),
        index.FilterField('ma_graduation_year'),

        index.SearchField('get_mphil_school_display'),
        index.SearchField('get_mphil_programme_display'),
        index.SearchField('mphil_graduation_year'),
        index.SearchField('mphil_dissertation_title'),
        index.SearchField('mphil_statement'),
        index.FilterField('mphil_in_show'),
        index.FilterField('mphil_school'),
        index.FilterField('mphil_programme'),
        index.FilterField('mphil_graduation_year'),
        index.FilterField('mphil_status'),
        index.FilterField('mphil_degree_type'),

        index.SearchField('get_phd_school_display'),
        index.SearchField('get_phd_programme_display'),
        index.SearchField('phd_graduation_year'),
        index.SearchField('phd_dissertation_title'),
        index.SearchField('phd_statement'),
        index.FilterField('phd_in_show'),
        index.FilterField('phd_school'),
        index.FilterField('phd_programme'),
        index.FilterField('phd_graduation_year'),
        index.FilterField('phd_status'),
        index.FilterField('phd_degree_type'),
    )

    @property
    def is_ma_student(self):
        return self.ma_school != ''

    @property
    def is_mphil_student(self):
        return self.mphil_school != ''

    @property
    def is_phd_student(self):
        return self.phd_school != ''

    def get_profiles(self):
        profiles = {}

        if self.is_phd_student:
            profiles['phd'] = {
                'name': "PhD",
                'school': self.phd_school,
                'school_display': self.get_phd_school_display(),
                'programme': self.phd_programme,
                'programme_display': self.get_phd_programme_display(),
                'start_year': self.phd_start_year,
                'graduation_year': self.phd_graduation_year,
                'in_show_': self.phd_in_show,
                'carousel_items': self.phd_carousel_items,
                'sponsors': self.phd_sponsors,
                'collaborators': self.phd_collaborators,
            }

        if self.is_mphil_student:
            profiles['mphil'] = {
                'name': "MPhil",
                'school': self.mphil_school,
                'school_display': self.get_mphil_school_display(),
                'programme': self.mphil_programme,
                'programme_display': self.get_mphil_programme_display(),
                'start_year': self.mphil_start_year,
                'graduation_year': self.mphil_graduation_year,
                'in_show_': self.mphil_in_show,
                'carousel_items': self.mphil_carousel_items,
                'sponsors': self.mphil_sponsors,
                'collaborators': self.mphil_collaborators,
            }

        if self.is_ma_student:
            profiles['ma'] = {
                'name': "MA",
                'school': self.ma_school,
                'school_display': self.get_ma_school_display(),
                'programme': self.ma_programme,
                'programme_display': self.get_ma_programme_display(),
                'start_year': self.ma_graduation_year,
                'graduation_year': self.ma_graduation_year,
                'in_show_': self.ma_in_show,
                'carousel_items': self.show_carousel_items,
                'sponsors': self.show_sponsors,
                'collaborators': self.show_collaborators,
            }

        return profiles

    def get_profile(self, profile=None):
        profiles = self.get_profiles()

        # Try to find the profile that was asked for
        if profile and profile in profiles:
            return profiles[profile]

        # Return the best profile
        if 'phd' in profiles:
            return profiles['phd']
        if 'mphil' in profiles:
            return profiles['mphil']
        if 'ma' in profiles:
            return profiles['ma']

    @property
    def school(self):
        profile = self.get_profile()

        if profile:
            return self.get_profile()['school']
        else:
            return ''

    @property
    def programme(self):
        profile = self.get_profile()

        if profile:
            return self.get_profile()['programme']
        else:
            return ''

    @property
    def search_name(self):
        profile = self.get_profile()
        if not profile:
            return "Student"

        current_year = timezone.now().year
        is_graduate = bool(profile['graduation_year'])
        if is_graduate and profile['graduation_year'] == str(timezone.now().year):
            is_graduate = False

        return profile['name'] + (" Graduate" if is_graduate else " Student")

    @property
    def profile_url(self):
        # Try to find a show profile
        if self.ma_in_show or self.mphil_in_show or self.phd_in_show:
            from rca_show.models import ShowIndexPage
            for show in ShowIndexPage.objects.filter(live=True):
                # Check if this student is in this show
                if not show.get_students().filter(id=self.id).exists():
                    continue

                # Get students URL in this show
                try:
                    url = show.get_student_url(self)
                    assert url is not None
                    return url
                except:
                    pass

        # Try to find a research profile
        if self.is_phd_student or self.is_mphil_student:
            for research_student_index in ResearchStudentIndex.objects.all():
                if research_student_index.all_students().filter(id=self.id).exists():
                    return research_student_index.url + self.slug + '/'

        # Try to find gallery profile
        if self.ma_in_show or self.mphil_in_show or self.phd_in_show:
            for gallery_page in GalleryPage.objects.all():
                if gallery_page.get_students()[0].filter(id=self.id).exists():
                    return gallery_page.url + self.slug + '/'

        # Cannot find any profiles, use regular url
        return self.url

    @property
    def search_url(self):
        # Use profile url in the search
        return self.profile_url

    @property
    def preview_modes(self):
        # Each ShowIndexPage can display a Student in a different styling
        # Find all ShowIndexPages and add them all to the list of page modes
        from rca_show.models import ShowIndexPage
        return super(NewStudentPage, self).preview_modes + [
            ('show:' + str(show_index.id), show_index.title)
            for show_index in ShowIndexPage.objects.all()
        ]

    def serve_preview(self, request, mode):
        # Check if a ShowIndexPage preview was selected
        from rca_show.models import ShowIndexPage
        if mode.startswith('show:'):
            show_index = ShowIndexPage.objects.get(id=int(mode[5:]))
            return show_index._serve_student(self.dummy_request(), self)

        return super(NewStudentPage, self).serve_preview(request, mode)

    def serve(self, request, view='standard'):
        if view not in ['standard', 'show', 'research']:
            raise Http404("Student view doesn't exist")

        # Insert view into TemplateResponse object
        response = super(NewStudentPage, self).serve(request)
        response.context_data['view'] = view
        return response

NewStudentPage.content_panels = [
    # General details
    FieldPanel('title', classname="full title"),
    MultiFieldPanel([
        FieldPanel('first_name'),
        FieldPanel('last_name'),
    ], "Full name"),
    ImageChooserPanel('profile_image'),
    ImageChooserPanel('postcard_image'),
    FieldPanel('statement', classname="full"),
    FieldPanel('twitter_handle'),
    FieldPanel('funding'),
    FieldPanel('innovation_rca_fellow'),
    InlinePanel('emails', label="Email"),
    InlinePanel('phones', label="Phone"),
    InlinePanel('websites', label="Website"),
    InlinePanel('previous_degrees', label="Previous degrees"),
    InlinePanel('exhibitions', label="Exhibitions"),
    InlinePanel('experiences', label="Experience"),
    InlinePanel('awards', label="Awards"),
    InlinePanel('publications', label="Publications"),
    InlinePanel('conferences', label="Conferences"),

    # MA details
    MultiFieldPanel([
        FieldPanel('ma_in_show'),
        FieldPanel('ma_school'),
        FieldPanel('ma_programme'),
        FieldPanel('ma_graduation_year'),
        FieldPanel('ma_specialism'),
    ], "MA details", classname="collapsible collapsed"),

    # Show details
    MultiFieldPanel([
        FieldPanel('show_work_type'),
        FieldPanel('show_work_title'),
        FieldPanel('show_work_location'),
        FieldPanel('show_work_description'),
        InlinePanel('show_carousel_items', label="Carousel image/video"),
        InlinePanel('show_collaborators', label="Collaborator"),
        InlinePanel('show_sponsors', label="Sponsor"),
    ], "MA Show details", classname="collapsible collapsed"),

    # MPhil details
    MultiFieldPanel([
        FieldPanel('mphil_in_show'),
        FieldPanel('mphil_school'),
        FieldPanel('mphil_programme'),
        FieldPanel('mphil_dissertation_title'),
        FieldPanel('mphil_statement'),
        FieldPanel('mphil_start_year'),
        FieldPanel('mphil_graduation_year'),
        FieldPanel('mphil_work_location'),
        FieldPanel('mphil_status'),
        FieldPanel('mphil_degree_type'),
        InlinePanel('mphil_carousel_items', label="Carousel image/video"),
        InlinePanel('mphil_collaborators', label="Collaborator"),
        InlinePanel('mphil_sponsors', label="Sponsor"),
        InlinePanel('mphil_supervisors', label="Supervisor"),
    ], "MPhil details", classname="collapsible collapsed"),

    # PhD details
    MultiFieldPanel([
        FieldPanel('phd_in_show'),
        FieldPanel('phd_school'),
        FieldPanel('phd_programme'),
        FieldPanel('phd_dissertation_title'),
        FieldPanel('phd_statement'),
        FieldPanel('phd_start_year'),
        FieldPanel('phd_graduation_year'),
        FieldPanel('phd_work_location'),
        FieldPanel('phd_status'),
        FieldPanel('phd_degree_type'),
        InlinePanel('phd_carousel_items', label="Carousel image/video"),
        InlinePanel('phd_collaborators', label="Collaborator"),
        InlinePanel('phd_sponsors', label="Sponsor"),
        InlinePanel('phd_supervisors', label="Supervisor"),
    ], "PhD details", classname="collapsible collapsed"),
]

NewStudentPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('show_on_homepage'),
        ImageChooserPanel('feed_image'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]

# When a user logs in, check for any NewStudentPages that have no owner but have an email address
# matching this user, and reassign them to be owned by this user
@receiver(user_logged_in)
def reassign_new_student_pages(sender, request, user, **kwargs):
    NewStudentPage.objects.filter(owner__isnull=True, emails__email__iexact=user.email).update(owner=user)


# == RCA Now page ==

class RcaNowPagePageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.RcaNowPage', related_name='carousel_items')


class RcaNowPageTag(TaggedItemBase):
    content_object = ParentalKey('rca.RcaNowPage', related_name='tagged_items')


class RcaNowPageArea(models.Model):
    page = ParentalKey('rca.RcaNowPage', related_name='areas')
    area = models.CharField(max_length=255, choices=AREA_CHOICES, help_text=help_text('rca.RcaNowPageArea', 'area'))

    panels = [FieldPanel('area')]


class RcaNowPageRelatedLink(Orderable):
    page = ParentalKey('rca.RcaNowPage', related_name='related_links')
    link = models.URLField(max_length=255, blank=True, help_text=help_text('rca.RcaNowPageRelatedLink', 'link'))

    panels = [FieldPanel('link')]


class RcaNowPage(Page, SocialFields):
    body = RichTextField(help_text=help_text('rca.RcaNowPage', 'body'))
    author = models.CharField(max_length=255, blank=True, help_text=help_text('rca.RcaNowPage', 'author'))
    date = models.DateField("Creation date", help_text=help_text('rca.RcaNowPage', 'date'))
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, help_text=help_text('rca.RcaNowPage', 'programme'))
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, help_text=help_text('rca.RcaNowPage', 'school'))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.RcaNowPage', 'show_on_homepage'))
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.RcaNowPage', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.RcaNowPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    tags = ClusterTaggableManager(through=RcaNowPageTag)

    # DELETED FIELDS
    area = models.CharField(max_length=255, choices=AREA_CHOICES, blank=True, editable=False, help_text=help_text('rca.RcaNowPage', 'area'))

    search_fields = Page.search_fields + (
        index.SearchField('body'),
        index.SearchField('author'),
        index.SearchField('get_programme_display'),
        index.SearchField('get_school_display'),
        index.SearchField('get_area_display'),
    )

    search_name = 'RCA Now'

    class Meta:
        verbose_name = 'RCA Now Page'

    def author_profile_page(self):
        """Return the profile page for the author of this post, if one exists (and is live)"""
        if self.owner:
            try:
                return StudentPage.objects.filter(live=True, owner=self.owner)[0]
            except IndexError:
                return None


RcaNowPage.content_panels = [
    InlinePanel('carousel_items', label="Carousel content"),
    FieldPanel('title', classname="full title"),
    FieldPanel('body', classname="full"),
    FieldPanel('author'),
    FieldPanel('date'),
    FieldPanel('school'),
    FieldPanel('programme'),
    InlinePanel('areas', label="Areas"),
    InlinePanel('related_links', label="Related links"),
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
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
    # InlinePanel('tagged_items', label='tag'),
    FieldPanel('tags'),
]


# == RCA Now index ==


class RcaNowIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.RcaNowIndex', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.RcaNowIndex', 'body'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.RcaNowIndex', 'twitter_feed'))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.RcaNowIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
        index.SearchField('body'),
    )

    search_name = None

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        programme = request.GET.get('programme')
        school = request.GET.get('school')
        area = request.GET.get('area')

        rca_now_items = RcaNowPage.objects.filter(live=True)

        # Run school, area and programme filters
        rca_now_items, filters = run_filters(rca_now_items, [
            ('school', 'school', school),
            ('programme', 'programme', programme),
            ('area', 'area', area),
        ])

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

        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, "rca/includes/rca_now_listing.html", {
                'self': self,
                'rca_now_items': rca_now_items,
                'filters': json.dumps(filters),
            })
        else:
            return render(request, self.template, {
                'self': self,
                'rca_now_items': rca_now_items,
                'filters': json.dumps(filters),
            })

    class Meta:
        verbose_name = 'RCA Now Index'

RcaNowIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
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
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]

# == RCA Blog page ==

class RcaBlogPagePageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.RcaBlogPage', related_name='carousel_items')


class RcaBlogPageTag(TaggedItemBase):
    content_object = ParentalKey('rca.RcaBlogPage', related_name='tagged_items')


class RcaBlogPageArea(models.Model):
    page = ParentalKey('rca.RcaBlogPage', related_name='areas')
    area = models.CharField(max_length=255, choices=AREA_CHOICES, help_text=help_text('rca.RcaBlogPageArea', 'area'))

    panels = [FieldPanel('area')]


class RcaBlogPage(Page, SocialFields):
    body = RichTextField(help_text=help_text('rca.RcaBlogPage', 'body'))
    author = models.CharField(max_length=255, blank=True, help_text=help_text('rca.RcaBlogPage', 'author'))
    date = models.DateField("Creation date", help_text=help_text('rca.RcaBlogPage', 'date'))
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True, help_text=help_text('rca.RcaBlogPage', 'programme'))
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True, help_text=help_text('rca.RcaBlogPage', 'school'))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.RcaBlogPage', 'show_on_homepage'))
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.RcaBlogPage', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, on_delete=models.SET_NULL, blank=True, related_name='+', help_text=help_text('rca.RcaBlogPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    tags = ClusterTaggableManager(through=RcaBlogPageTag)

    # DELETED FIELDS
    area = models.CharField(max_length=255, choices=AREA_CHOICES, blank=True, editable=False, help_text=help_text('rca.RcaBlogPage', 'area'))

    search_fields = Page.search_fields + (
        index.SearchField('body'),
        index.SearchField('author'),
        index.SearchField('get_programme_display'),
        index.SearchField('get_school_display'),
        index.SearchField('get_area_display'),
    )

    search_name = 'RCA Blog'

    class Meta:
        verbose_name = 'Blog Page'

    def author_profile_page(self):
        """Return the profile page for the author of this post, if one exists (and is live)"""
        if self.owner:
            try:
                return StudentPage.objects.filter(live=True, owner=self.owner)[0]
            except IndexError:
                return None

    def blog_index(self):
        """Return the parent blog index for the blog page, so that it can be displayed in the Homepage packery area"""
        return self.get_ancestors().type(RcaBlogIndex).last()

    def get_related_blogs(self, count=4):
        siblings = self.get_siblings()
        related_blogs = RcaBlogPage.objects.filter(live=True, id__in=siblings).order_by('-date')
        related_blogs = related_blogs.exclude(id=self.id)
        return related_blogs[:count]


RcaBlogPage.content_panels = [
    InlinePanel('carousel_items', label="Carousel content"),
    FieldPanel('title', classname="full title"),
    FieldPanel('body', classname="full"),
    FieldPanel('author'),
    FieldPanel('date'),
    FieldPanel('school'),
    FieldPanel('programme'),
    InlinePanel('areas', label="Areas"),
    FieldPanel('twitter_feed'),
]

RcaBlogPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('show_on_homepage'),
        ImageChooserPanel('feed_image'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
    # InlinePanel('tagged_items', label='tag'),
    FieldPanel('tags'),
]


# == RCA Blog index ==


class RcaBlogIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.RcaBlogIndex', 'intro'), null=True, blank=True)
    body = RichTextField(help_text=help_text('rca.RcaBlogIndex', 'body'), null=True, blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.RcaBlogIndex', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, on_delete=models.SET_NULL, blank=True, related_name='+', help_text=help_text('rca.RcaBlogIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
        index.SearchField('body'),
    )

    search_name = None

    class Meta:
        verbose_name = 'Blog Index'

    def get_blog_items(self, tag=None):
        blog_items = RcaBlogPage.objects.filter(live=True, path__startswith=self.path)

        # Filter by tag
        if tag is not None and len(tag):
            blog_items = blog_items.filter(tagged_items__tag__slug=tag)

        return blog_items

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        # programme = request.GET.get('programme')
        # school = request.GET.get('school')
        # area = request.GET.get('area')
        tag = request.GET.get('tag', None)

        rca_blog_items = self.get_blog_items(tag=tag)

        # Run school, area and programme filters
        # rca_blog_items, filters = run_filters(rca_blog_items, [
        #     ('school', 'school', school),
        #     ('programme', 'programme', programme),
        #     ('area', 'area', area),
        # ])

        rca_blog_items = rca_blog_items.order_by('-date')

        page = request.GET.get('page')
        paginator = Paginator(rca_blog_items, 10)  # Show 10 rca blog items per page
        try:
            rca_blog_items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            rca_blog_items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            rca_blog_items = paginator.page(paginator.num_pages)

        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, "rca/includes/rca_blog_listing.html", {
                'self': self,
                'rca_blog_items': rca_blog_items,
                'tag': tag,
                #'filters': json.dumps(filters),
            })
        else:
            return render(request, self.template, {
                'self': self,
                'rca_blog_items': rca_blog_items,
                'tag': tag,
                #'filters': json.dumps(filters),
            })

    def get_popular_tags(self):
        # Get Queryset of RcaBlogTags for all blog items
        all_tags = RcaBlogPageTag.objects.filter(content_object__in=self.get_blog_items())

        # Get a ValuesQuerySet of tags ordered by most popular
        popular_tags = all_tags.values('tag').annotate(item_count=models.Count('tag')).order_by('-item_count')

        # Return first 10 popular tags as tag objects
        # Getting them individually to preserve the order
        return [Tag.objects.get(id=tag['tag']) for tag in popular_tags[:10]]

RcaBlogIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    FieldPanel('twitter_feed'),
]

RcaBlogIndex.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
        FieldPanel('search_description'),
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
    person = models.ForeignKey(Page, null=True, blank=True, related_name='+', help_text=help_text('rca.ResearchItemCreator', 'person', default="Choose an existing person's page, or enter a name manually below (which will not be linked)."))
    manual_person_name= models.CharField(max_length=255, blank=True, help_text=help_text('rca.ResearchItemCreator', 'manual_person_name', default="Only required if the creator has no page of their own to link to"))

    panels=[
        PageChooserPanel('person'),
        FieldPanel('manual_person_name')
    ]

class ResearchItemLink(Orderable):
    page = ParentalKey('rca.ResearchItem', related_name='links')
    link = models.URLField(help_text=help_text('rca.ResearchItemLink', 'link'))
    link_text = models.CharField(max_length=255, help_text=help_text('rca.ResearchItemLink', 'link_text'))

    panels=[
        FieldPanel('link'),
        FieldPanel('link_text')
    ]

class ResearchItem(Page, SocialFields):
    subtitle = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ResearchItem', 'subtitle'))
    research_type = models.CharField(max_length=255, choices=RESEARCH_TYPES_CHOICES, help_text=help_text('rca.ResearchItem', 'research_type'))
    ref = models.BooleanField(default=False, blank=True, help_text=help_text('rca.ResearchItem', 'ref'))
    year = models.CharField(max_length=4, help_text=help_text('rca.ResearchItem', 'year'))
    description = RichTextField(help_text=help_text('rca.ResearchItem', 'description'))
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, help_text=help_text('rca.ResearchItem', 'school'))
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True, help_text=help_text('rca.ResearchItem', 'programme'))
    work_type = models.CharField(max_length=255, choices=WORK_TYPES_CHOICES, help_text=help_text('rca.ResearchItem', 'work_type'))
    work_type_other = models.CharField("'Other' work type", max_length=255, blank=True, help_text=help_text('rca.ResearchItem', 'work_type_other'))
    theme = models.CharField(max_length=255, choices=WORK_THEME_CHOICES, blank=True, help_text=help_text('rca.ResearchItem', 'theme'))
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ResearchItem', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    rca_content_id = models.CharField(max_length=255, blank=True, editable=False) # for import
    eprintid = models.CharField(max_length=255, blank=True, editable=False) # for import
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.ResearchItem', 'show_on_homepage'))
    random_order = models.IntegerField(null=True, blank=True, editable=False)
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ResearchItem', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('subtitle'),
        index.SearchField('get_research_type_display'),
        index.SearchField('description'),
        index.SearchField('get_school_display'),
        index.SearchField('get_programme_display'),
        index.SearchField('get_work_type_display'),
        index.SearchField('work_type_other'),
        index.SearchField('get_theme_display'),
    )

    search_name = 'Research'

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        # Get related research
        research_items = ResearchItem.objects.filter(live=True).order_by('random_order')
        if self.programme:
            research_items = research_items.filter(programme__in=get_programme_synonyms(self.programme))
        else:
            research_items = research_items.filter(school=self.school)

        paginator = Paginator(research_items, 4)

        page = request.GET.get('page')
        try:
            research_items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            research_items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            research_items = paginator.page(paginator.num_pages)

        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, "rca/includes/research_listing.html", {
                'self': self,
                'research_items': research_items
            })
        else:
            return render(request, self.template, {
                'self': self,
                'research_items': research_items
            })

    def get_related_news(self, count=4):
        return NewsItem.get_related(
            areas=['research'],
            programmes=get_programme_synonyms(self.programme) if self.programme else None,
            schools=([self.school] if self.school else None),
            count=count,
        )

ResearchItem.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('subtitle'),
    InlinePanel('carousel_items', label="Carousel content"),
    FieldPanel('research_type'),
    InlinePanel('creator', label="Creator"),
    FieldPanel('ref'),
    FieldPanel('year'),
    FieldPanel('school'),
    FieldPanel('programme'),
    FieldPanel('work_type'),
    FieldPanel('work_type_other'),
    FieldPanel('theme'),
    FieldPanel('description'),
    InlinePanel('links', label="Links"),
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
        FieldPanel('search_description'),
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
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ResearchInnovationPageTeaser', 'image'))
    url = models.URLField(blank=True, help_text=help_text('rca.ResearchInnovationPageTeaser', 'url'))
    title = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ResearchInnovationPageTeaser', 'title'))
    text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ResearchInnovationPageTeaser', 'text'))

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('url'),
        FieldPanel('title', classname="full title"),
        FieldPanel('text'),
    ]

class ResearchInnovationPageRelatedLink(Orderable, RelatedLinkMixin):
    page = ParentalKey('rca.ResearchInnovationPage', related_name='related_links')

class ResearchInnovationPageContactPhone(Orderable):
    page = ParentalKey('rca.ResearchInnovationPage', related_name='contact_phone')
    phone_number = models.CharField(max_length=255, help_text=help_text('rca.ResearchInnovationPageContactPhone', 'phone_number'))

    panels = [
        FieldPanel('phone_number')
    ]

class ResearchInnovationPageContactEmail(Orderable):
    page = ParentalKey('rca.ResearchInnovationPage', related_name='contact_email')
    email_address = models.CharField(max_length=255, help_text=help_text('rca.ResearchInnovationPageContactEmail', 'email_address'))

    panels = [
        FieldPanel('email_address')
    ]

class ResearchInnovationPageCurrentResearch(Orderable):
    page = ParentalKey('rca.ResearchInnovationPage', related_name='current_research')
    link = models.ForeignKey(Page, null=True, blank=True, related_name='+', help_text=help_text('rca.ResearchInnovationPageCurrentResearch', 'link'))

    panels = [
        PageChooserPanel('link'),
    ]

    class Meta:
        # needs to be shortened to avoid hitting limit on the permissions table - https://code.djangoproject.com/ticket/8548
        verbose_name = "research innov. page current research"

class ResearchInnovationPageAd(Orderable):
    page = ParentalKey('rca.ResearchInnovationPage', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.ResearchInnovationPageAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class ResearchInnovationPage(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.ResearchInnovationPage', 'intro'), blank=True)
    intro_link = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ResearchInnovationPage', 'intro_link'))
    teasers_title = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ResearchInnovationPage', 'teasers_title'))
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ResearchInnovationPage', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ResearchInnovationPage', 'background_image', default="The full bleed image in the background"))
    contact_title = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ResearchInnovationPage', 'contact_title'))
    contact_address = models.TextField(blank=True, help_text=help_text('rca.ResearchInnovationPage', 'contact_address'))
    contact_link = models.URLField(blank=True, help_text=help_text('rca.ResearchInnovationPage', 'contact_link'))
    contact_link_text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ResearchInnovationPage', 'contact_link_text'))
    news_carousel_area = models.CharField(max_length=255, choices=AREA_CHOICES, blank=True, help_text=help_text('rca.ResearchInnovationPage', 'news_carousel_area'))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ResearchInnovationPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
    )

    search_name = None

ResearchInnovationPage.content_panels = [
    FieldPanel('title', classname="full title"),
    MultiFieldPanel([
        FieldPanel('intro', classname="full"),
        PageChooserPanel('intro_link'),
    ],'Introduction'),
    InlinePanel('current_research', label="Current research"),
    InlinePanel('carousel_items', label="Carousel content"),
    FieldPanel('teasers_title'),
    InlinePanel('teasers', label="Teaser content"),
    InlinePanel('related_links', label="Related links"),
    InlinePanel('manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
    ImageChooserPanel('background_image'),
    MultiFieldPanel([
        FieldPanel('contact_title'),
        FieldPanel('contact_address'),
        FieldPanel('contact_link'),
        FieldPanel('contact_link_text'),

    ],'Contact'),
    InlinePanel('contact_phone', label="Contact phone number"),
    InlinePanel('contact_email', label="Contact email address"),
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
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]


# == Current research page ==
class CurrentResearchPageAd(Orderable):
    page = ParentalKey('rca.CurrentResearchPage', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.CurrentResearchPageAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class CurrentResearchPage(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.CurrentResearchPage', 'intro'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.CurrentResearchPage', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.CurrentResearchPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    indexed = False

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        research_type = request.GET.get('research_type')
        school = request.GET.get('school')
        theme = request.GET.get('theme')
        work_type = request.GET.get('work_type')

        research_items = ResearchItem.objects.filter(live=True).order_by('random_order')

        # Run filters
        research_items, filters = run_filters(research_items, [
            ('research_type', 'research_type', research_type),
            ('school', 'school', school),
            ('theme', 'theme', theme),
            ('work_type', 'work_type', work_type),
        ])

        research_items.order_by('-year')

        per_page = 8
        page = request.GET.get('page')
        paginator = Paginator(research_items, per_page)  # Show 8 research items per page
        try:
            research_items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            research_items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            research_items = paginator.page(paginator.num_pages)

        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, "rca/includes/research_listing.html", {
                'self': self,
                'research_items': research_items,
                'filters': json.dumps(filters),
                'per_page': per_page,
            })
        else:
            return render(request, self.template, {
                'self': self,
                'research_items': research_items,
                'filters': json.dumps(filters),
                'per_page': per_page,
            })

CurrentResearchPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel('manual_adverts', label="Manual adverts"),
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
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]

# == Gallery Page ==

class GalleryPageRelatedLink(Orderable, RelatedLinkMixin):
    page = ParentalKey('rca.GalleryPage', related_name='related_links')

class GalleryPage(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.GalleryPage', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.GalleryPage', 'body'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.GalleryPage', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.GalleryPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
        index.SearchField('body'),
    )

    search_name = 'Gallery'

    def student_which_profile(self, student, ma_students_q, mphil_students_q, phd_students_q):
        students = NewStudentPage.objects.filter(live=True)

        # Check if student is in phd students
        if students.filter(phd_students_q).filter(pk=student.pk).exists():
            return 'phd'

        # Check if student is in mphil students
        if students.filter(mphil_students_q).filter(pk=student.pk).exists():
            return 'mphil'

        # Check if student is in ma students
        if students.filter(ma_students_q).filter(pk=student.pk).exists():
            return 'ma'

    def get_students_q(self, school=None, programme=None, year=None):
        ma_students_q = ~models.Q(ma_school='') & models.Q(ma_in_show=True)
        mphil_students_q = ~models.Q(mphil_school='') & ~models.Q(mphil_graduation_year='') & models.Q(mphil_in_show=True)
        phd_students_q = ~models.Q(phd_school='') & ~models.Q(phd_graduation_year='') & models.Q(phd_in_show=True)

        # Run filters
        ma_filters = run_filters_q(NewStudentPage, ma_students_q, [
            ('school', 'ma_school', school),
            ('programme', 'ma_programme', programme),
            ('year', 'ma_graduation_year', year),
        ])
        mphil_filters = run_filters_q(NewStudentPage, mphil_students_q, [
            ('school', 'mphil_school', school),
            ('programme', 'mphil_programme', programme),
            ('year', 'mphil_graduation_year', year),
        ])
        phd_filters = run_filters_q(NewStudentPage, phd_students_q, [
            ('school', 'phd_school', school),
            ('programme', 'phd_programme', programme),
            ('year', 'phd_graduation_year', year),
        ])

        # Combine filters
        filters = combine_filters(ma_filters, mphil_filters, phd_filters)

        # Add combined filters to both groups
        ma_students_q &= get_filters_q(filters, {
            'school': 'ma_school',
            'programme': 'ma_programme',
            'year': 'ma_graduation_year',
        })
        mphil_students_q &= get_filters_q(filters, {
            'school': 'mphil_school',
            'programme': 'mphil_programme',
            'year': 'mphil_graduation_year',
        })
        phd_students_q &= get_filters_q(filters, {
            'school': 'phd_school',
            'programme': 'phd_programme',
            'year': 'phd_graduation_year',
        })

        return ma_students_q, mphil_students_q, phd_students_q, filters

    def get_students(self, school=None, programme=None, year=None):
        ma_students_q, mphil_students_q, phd_students_q, filters = self.get_students_q(school, programme, year)
        return NewStudentPage.objects.filter(live=True).filter(ma_students_q | mphil_students_q | phd_students_q), filters

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        # Get filter parameters
        school = request.GET.get('school')
        programme = request.GET.get('programme')
        year = request.GET.get('degree_year') or '2013'

        # Get students
        ma_students_q, mphil_students_q, phd_students_q, filters = self.get_students_q(school, programme, year)
        students = NewStudentPage.objects.filter(live=True).filter(ma_students_q | mphil_students_q | phd_students_q)

        # Find year options
        year_options = []
        for fil in filters:
            if fil['name'] == 'year':
                year_options = fil['options']
                break

        # Randomly order students
        students = students.extra(
            select={
                '_year': "CASE WHEN phd_graduation_year = '' THEN CASE WHEN mphil_graduation_year = '' THEN ma_graduation_year ELSE mphil_graduation_year END ELSE phd_graduation_year END"
            },
            order_by=['-_year', 'random_order'],
        ).distinct()

        # Pagination
        page = request.GET.get('page')
        paginator = Paginator(students, 5)  # Show 5 gallery items per page
        try:
            students = paginator.page(page)
        except PageNotAnInteger:
            students = paginator.page(1)
        except EmptyPage:
            students = paginator.page(paginator.num_pages)

        # Add profile to students
        for student in students:
            student.profile = student.get_profile(self.student_which_profile(student, ma_students_q, mphil_students_q, phd_students_q))

        # Get template
        if request.is_ajax() and 'pjax' not in request.GET:
            template = 'rca/includes/gallery_listing.html'
        else:
            template = self.template

        # Render response
        return render(request, template, {
            'self': self,
            'gallery_items': students,
            'filters': json.dumps(filters),
            'years': reversed(sorted(year_options)),
            'selected_year': year,
        })

    def route(self, request, path_components):
        # If there are any path components, try checking if one if them is a student in the gallery
        # If so, re route through the student page
        if len(path_components) == 1:
            try:
                student_page = self.get_students()[0].get(slug=path_components[0])
                return RouteResult(student_page.specific, kwargs={'view': 'show'})
            except NewStudentPage.DoesNotExist:
                pass

        return super(GalleryPage, self).route(request, path_components)


GalleryPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
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
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]

# == Contact Us page ==

class ContactUsPage(Page, SocialFields):
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ContactUsPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

ContactUsPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]


# == Online Express form page ==

class OEFormPage(Page, SocialFields):
    form_id = models.CharField(max_length=255, help_text="The long number in brackets from the generated JavaScript snippet")

    # fields copied from StandrdPage
    intro = RichTextField(blank=True)
    body = RichTextField(blank=True)
    strapline = models.CharField(max_length=255, blank=True)
    middle_column_body = RichTextField(blank=True)
    show_on_homepage = models.BooleanField(default=False)
    feed_image = models.ForeignKey('rca.RcaImage', null=True, on_delete=models.SET_NULL, blank=True, related_name='+', help_text="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio.")
    data_protection = RichTextField(blank=True)

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
        index.SearchField('body'),
    )

    search_name = None

OEFormPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('strapline', classname="full"),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    FieldPanel('middle_column_body', classname="full"),
    FieldPanel('form_id'),
    FieldPanel('data_protection', classname="full"),
]

OEFormPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('show_on_homepage'),
        ImageChooserPanel('feed_image'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]

# == Donation page ==


class DonationPage(Page, SocialFields):
    redirect_to_when_done = models.ForeignKey(Page, null=True, blank=False, on_delete=models.PROTECT, related_name='+', help_text=help_text('rca.DonationPage', 'redirect_to_when_done'))
    payment_description = models.CharField(max_length=255, blank=True, help_text=help_text('rca.DonationPage', 'payment_description', default="This value will be stored along with each donation made on this page to help ditinguish them from donations on other pages."))

    # fields copied from StandrdPage
    intro = RichTextField(help_text=help_text('rca.DonationPage', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.DonationPage', 'body'), blank=True)
    strapline = models.CharField(max_length=255, blank=True, help_text=help_text('rca.DonationPage', 'strapline'))
    middle_column_body = RichTextField(blank=True, help_text=help_text('rca.DonationPage', 'middle_column_body'))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.DonationPage', 'show_on_homepage'))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.DonationPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
        index.SearchField('body'),
    )

    search_name = None

    class Meta:
        verbose_name = "RCA USA Stripe donation page"

    def serve(self, request):
        stripe.api_key = settings.STRIPE_SECRET_KEY

        if request.method == "POST":
            form = DonationForm(request.POST)
            if form.is_valid():
                error_metadata = ""
                try:
                    metadata = form.cleaned_data.get('metadata', {})
                    error_metadata = str(metadata)

                    customer = stripe.Customer.create(
                        card=form.cleaned_data.get('stripe_token'),
                        email=metadata.get("email", "")
                    )

                    # When exporting the payments from the dashboard
                    # the metadata field is not exported but the description is,
                    # so we duplicate the metadata there as well.
                    charge = stripe.Charge.create(
                        customer=customer.id,
                        amount=form.cleaned_data.get('amount'),  # amount in cents (converted by the form)
                        currency="usd",
                        description=self.payment_description,
                        metadata=metadata,
                    )
                    return HttpResponseRedirect(self.redirect_to_when_done.url)
                except stripe.CardError, e:
                    # CardErrors are displayed to the user, but we notify admins as well
                    mail_exception(e, prefix=" [stripe] ", message=error_metadata)
                    logging.error("[stripe] " + error_metadata, exc_info=full_exc_info())
                    messages.error(request, e.json_body['error']['message'])
                except Exception, e:
                    # for other exceptions we send emails to admins and display a user freindly error message
                    # InvalidRequestError (if token is used more than once), APIError (server is not reachable), AuthenticationError
                    mail_exception(e, prefix=" [stripe] ", message=error_metadata)
                    logging.error("[stripe] " + error_metadata, exc_info=full_exc_info())
                    messages.error(request, "There was a problem processing your payment. Please try again later.")
        else:
            towards = request.GET.get('to')
            form = DonationForm(initial={'donation_for': towards})
            form = DonationForm()

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
    # InlinePanel('carousel_items', label="Carousel content"),
    # InlinePanel('related_links', label="Related links"),
    # InlinePanel('reusable_text_snippets', label="Reusable text snippet"),
    # InlinePanel('documents', label="Document"),
    # InlinePanel('quotations', label="Quotation"),
    # InlinePanel('images', label="Middle column image"),
    # InlinePanel('manual_adverts', label="Manual adverts"),
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
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]


# == InnovationRCA Project page ==

class InnovationRCAProjectCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.InnovationRCAProject', related_name='carousel_items')

class InnovationRCAProjectCreator(Orderable):
    page = ParentalKey('rca.InnovationRCAProject', related_name='creator')
    person = models.ForeignKey(Page, null=True, blank=True, related_name='+', help_text=help_text('rca.InnovationRCAProjectCreator', 'person', default="Choose an existing person's page, or enter a name manually below (which will not be linked)."))
    manual_person_name= models.CharField(max_length=255, blank=True, help_text=help_text('rca.InnovationRCAProjectCreator', 'manual_person_name', default="Only required if the creator has no page of their own to link to"))

    panels=[
        PageChooserPanel('person'),
        FieldPanel('manual_person_name')
    ]

class InnovationRCAProjectLink(Orderable):
    page = ParentalKey('rca.InnovationRCAProject', related_name='links')
    link = models.URLField(help_text=help_text('rca.InnovationRCAProjectLink', 'link'))
    link_text = models.CharField(max_length=255, help_text=help_text('rca.InnovationRCAProjectLink', 'link_text'))

    panels=[
        FieldPanel('link'),
        FieldPanel('link_text')
    ]

class InnovationRCAProject(Page, SocialFields):
    subtitle = models.CharField(max_length=255, blank=True, help_text=help_text('rca.InnovationRCAProject', 'subtitle'))
    year = models.CharField(max_length=4, blank=True, help_text=help_text('rca.InnovationRCAProject', 'year'))
    description = RichTextField(help_text=help_text('rca.InnovationRCAProject', 'description'))
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True, help_text=help_text('rca.InnovationRCAProject', 'school'))
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True, help_text=help_text('rca.InnovationRCAProject', 'programme'))
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.InnovationRCAProject', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.InnovationRCAProject', 'show_on_homepage'))
    project_type = models.CharField(max_length=255, choices=INNOVATIONRCA_PROJECT_TYPES_CHOICES, help_text=help_text('rca.InnovationRCAProject', 'project_type'))
    project_ended = models.BooleanField(default=False, help_text=help_text('rca.InnovationRCAProject', 'project_ended'))
    random_order = models.IntegerField(null=True, blank=True, editable=False)
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.InnovationRCAProject', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('subtitle'),
        index.SearchField('get_research_type_display'),
        index.SearchField('description'),
        index.SearchField('get_school_display'),
        index.SearchField('get_programme_display'),
        index.SearchField('get_project_type_display'),
    )

    search_name = 'InnovationRCA Project'

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        # Get related research
        projects = InnovationRCAProject.objects.filter(live=True).order_by('random_order')
        projects = projects.filter(project_type=self.project_type)
        if self.programme:
            projects = projects.filter(programme__in=get_programme_synonyms(self.programme))
        elif self.school:
            projects = projects.filter(school=self.school)

        paginator = Paginator(projects, 4)

        page = request.GET.get('page')
        try:
            projects = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            projects = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            projects = paginator.page(paginator.num_pages)

        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, "rca/includes/innovation_rca_listing.html", {
                'self': self,
                'projects': projects
            })
        else:
            return render(request, self.template, {
                'self': self,
                'projects': projects
            })

    def get_related_news(self, count=4):
        return NewsItem.get_related(
            areas=['research'],
            programmes=get_programme_synonyms(self.programme) if self.programme else None,
            schools=([self.school] if self.school else None),
            count=count,
        )

    class Meta:
        verbose_name = "InnovationRCA Project"

InnovationRCAProject.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('subtitle'),
    InlinePanel('carousel_items', label="Carousel content"),
    InlinePanel('creator', label="Creator"),
    FieldPanel('year'),
    FieldPanel('school'),
    FieldPanel('programme'),
    FieldPanel('project_type'),
    FieldPanel('project_ended'),
    FieldPanel('description'),
    InlinePanel('links', label="Links"),
    FieldPanel('twitter_feed'),
]

InnovationRCAProject.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('show_on_homepage'),
        ImageChooserPanel('feed_image'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]


# == InnovationRCA Index page ==

class InnovationRCAIndexAd(Orderable):
    page = ParentalKey('rca.InnovationRCAIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.InnovationRCAIndexAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class InnovationRCAIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.InnovationRCAIndex', 'intro'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.InnovationRCAIndex', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.InnovationRCAIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    indexed = False

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        # Get list of live projects
        projects = InnovationRCAProject.objects.filter(live=True).order_by('random_order')

        # Apply filters
        project_type = request.GET.get('project_type', None)
        current_past = request.GET.get('current_past', None)

        if current_past == 'past':
            project_ended = True
        elif current_past == 'current':
            project_ended = False
        else:
            project_ended = None

        if project_type:
            projects = projects.filter(project_type=project_type)
        if project_ended is not None:
            projects = projects.filter(project_ended=project_ended)

        # Pagination
        page = request.GET.get('page')
        paginator = Paginator(projects, 8)  # Show 8 projects per page
        try:
            projects = paginator.page(page)
        except PageNotAnInteger:
            projects = paginator.page(1)
        except EmptyPage:
            projects = paginator.page(paginator.num_pages)

        # Find template
        if request.is_ajax() and 'pjax' not in request.GET:
            template = "rca/includes/innovation_rca_listing.html"
        else:
            template = self.template

        # Render
        return render(request, template, {
            'self': self,
            'projects': projects,
        })

    class Meta:
        verbose_name = "InnovationRCA Project Index"

InnovationRCAIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel('manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
]

InnovationRCAIndex.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]

# # == SustainRCA Project Page ==

class SustainRCAProjectCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.SustainRCAProject', related_name='carousel_items')

class SustainRCAProjectCreator(Orderable):
    page = ParentalKey('rca.SustainRCAProject', related_name='creator')
    person = models.ForeignKey(Page, null=True, blank=True, related_name='+', help_text=help_text('rca.SustainRCAProjectCreator', 'person', default="Choose an existing person's page, or enter a name manually below (which will not be linked)."))
    manual_person_name= models.CharField(max_length=255, blank=True, help_text=help_text('rca.SustainRCAProjectCreator', 'manual_person_name', default="Only required if the creator has no page of their own to link to"))

    panels=[
        PageChooserPanel('person'),
        FieldPanel('manual_person_name')
    ]

class SustainRCAProjectLink(Orderable):
    page = ParentalKey('rca.SustainRCAProject', related_name='links')
    link = models.URLField(help_text=help_text('rca.SustainRCAProjectLink', 'link'))
    link_text = models.CharField(max_length=255, help_text=help_text('rca.SustainRCAProjectLink', 'link_text'))

    panels=[
        FieldPanel('link'),
        FieldPanel('link_text')
    ]

class SustainRCAProject(Page, SocialFields):
    subtitle = models.CharField(max_length=255, blank=True, help_text=help_text('rca.SustainRCAProject', 'subtitle'))
    category = models.CharField(max_length=255, blank=True, choices=SUSTAINRCA_CATEGORY_CHOICES)
    year = models.CharField(max_length=4, blank=True, help_text=help_text('rca.SustainRCAProject', 'year'))
    description = RichTextField(help_text=help_text('rca.SustainRCAProject', 'description'))
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True, help_text=help_text('rca.SustainRCAProject', 'school'))
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True, help_text=help_text('rca.SustainRCAProject', 'programme'))
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.SustainRCAProject', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.SustainRCAProject', 'show_on_homepage'))
    random_order = models.IntegerField(null=True, blank=True, editable=False)
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.SustainRCAProject', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('subtitle'),
        index.SearchField('get_research_type_display'),
        index.SearchField('description'),
        index.SearchField('get_school_display'),
        index.SearchField('get_programme_display'),
        index.SearchField('get_category_display'),
    )

    search_name = 'SustainRCA Project'

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        # Get related research
        projects = SustainRCAProject.objects.filter(live=True).order_by('random_order')
        projects = projects.filter(category=self.category)
        if self.programme:
            projects = projects.filter(programme__in=get_programme_synonyms(self.programme))
        elif self.school:
            projects = projects.filter(school=self.school)

        paginator = Paginator(projects, 4)

        page = request.GET.get('page')
        try:
            projects = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            projects = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            projects = paginator.page(paginator.num_pages)

        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, "rca/includes/sustain_rca_listing.html", {
                'self': self,
                'projects': projects
            })
        else:
            return render(request, self.template, {
                'self': self,
                'projects': projects
            })

    def get_related_news(self, count=4):
        return NewsItem.get_related(
            areas=['research'],
            programmes=get_programme_synonyms(self.programme) if self.programme else None,
            schools=([self.school] if self.school else None),
            count=count,
        )

    class Meta:
        verbose_name = "SustainRCA Project"

SustainRCAProject.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('subtitle'),
    InlinePanel('carousel_items', label="Carousel content"),
    InlinePanel('creator', label="Creator"),
    FieldPanel('year'),
    FieldPanel('school'),
    FieldPanel('programme'),
    FieldPanel('description'),
    FieldPanel('category'),
    InlinePanel('links', label="Links"),
    FieldPanel('twitter_feed'),
]

SustainRCAProject.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('show_on_homepage'),
        ImageChooserPanel('feed_image'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]


# == SustainRCA Index page ==

class SustainRCAIndexAd(Orderable):
    page = ParentalKey('rca.SustainRCAIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+')

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class SustainRCAIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.SustainRCAIndex', 'intro'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.SustainRCAIndex', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.SustainRCAIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    indexed = False

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        selected_year = request.GET.get('year', None)
        selected_category = request.GET.get('category', None)
        selected_programme = request.GET.get('programme', None)

        projects = SustainRCAProject.objects.filter(live=True)
        projects, filters = run_filters(projects, [
            ('year', 'year', selected_year),
            ('category', 'category', selected_category),
            ('programme', 'programme', selected_programme)
        ])
        projects = projects.order_by('random_order')

        years = projects.values_list('year', flat=True).distinct()

        # Pagination
        page = request.GET.get('page')
        paginator = Paginator(projects, 8)  # Show 8 projects per page
        try:
            projects = paginator.page(page)
        except PageNotAnInteger:
            projects = paginator.page(1)
        except EmptyPage:
            projects = paginator.page(paginator.num_pages)

        # Find template
        if request.is_ajax() and 'pjax' not in request.GET:
            template = "rca/includes/sustain_rca_listing.html"
        else:
            template = self.template

        # Render
        return render(request, template, {
            'self': self,
            'projects': projects,
            'years': years,
            'filters': json.dumps(filters),
        })

    class Meta:
        verbose_name = "SustainRCA Project Index"

SustainRCAIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel('manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
]

SustainRCAIndex.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]


# # == ReachOutRCA Project page ==

class ReachOutRCAProjectCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.ReachOutRCAProject', related_name='carousel_items')

class ReachOutRCAWorkshopLeader(Orderable):
    page = ParentalKey('rca.ReachOutRCAProject', related_name='leader')
    person = models.ForeignKey(Page, null=True, blank=True, related_name='+', help_text=help_text('rca.ReachOutRCAWorkshopLeader', 'person', default="Choose an existing person's page, or enter a name manually below (which will not be linked)."))
    manual_person_name= models.CharField(max_length=255, blank=True, help_text=help_text('rca.ReachOutRCAWorkshopLeader', 'person', default="Only required if the creator has no page of their own to link to"))

    panels=[
        PageChooserPanel('person'),
        FieldPanel('manual_person_name')
    ]

class ReachOutRCAWorkshopAssistant(Orderable):
    page = ParentalKey('rca.ReachOutRCAProject', related_name='assistant')
    person = models.ForeignKey(Page, null=True, blank=True, related_name='+', help_text=help_text('rca.ReachOutRCAWorkshopAssistant', 'person', default="Choose an existing person's page, or enter a name manually below (which will not be linked)."))
    manual_person_name= models.CharField(max_length=255, blank=True, help_text=help_text('rca.ReachOutRCAWorkshopAssistant', 'person', default="Only required if the creator has no page of their own to link to"))

    panels=[
        PageChooserPanel('person'),
        FieldPanel('manual_person_name')
    ]

class ReachOutRCAProjectLink(Orderable):
    page = ParentalKey('rca.ReachOutRCAProject', related_name='links')
    link = models.URLField(blank=True, help_text=help_text('rca.ReachOutRCAProjectLink', 'link'))
    link_text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ReachOutRCAProjectLink', 'link_text'))

    panels=[
        FieldPanel('link'),
        FieldPanel('link_text')
    ]

class ReachOutRCAThemes(Orderable):
    page = ParentalKey('rca.ReachOutRCAProject', related_name='themes')
    theme = models.CharField(max_length=255, blank=True, choices=REACHOUT_THEMES_CHOICES, help_text=help_text('rca.ReachOutRCAThemes', 'theme'))

    panels=[
        FieldPanel('theme')
    ]

class ReachOutRCAParticipants(Orderable):
    page = ParentalKey('rca.ReachOutRCAProject', related_name='participants')
    participant = models.CharField(max_length=255, blank=True, choices=REACHOUT_PARTICIPANTS_CHOICES, help_text=help_text('rca.ReachOutRCAParticipants', 'participant'))

    panels=[
        FieldPanel('participant')
    ]

class ReachOutRCAPartnership(Orderable):
    page = ParentalKey('rca.ReachOutRCAProject', related_name='partnerships')
    partnership = models.CharField(max_length=255, blank=True, choices=REACHOUT_PARTNERSHIPS_CHOICES, help_text=help_text('rca.ReachOutRCAPartnership', 'partnership'))

    panels=[
        FieldPanel('partnership')
    ]

class ReachOutRCAQuotation(Orderable):
    page = ParentalKey('rca.ReachOutRCAProject', related_name='quotations')
    quotation = models.TextField(help_text=help_text('rca.ReachOutRCAQuotation', 'quotation'))
    quotee = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ReachOutRCAQuotation', 'quotee'))
    quotee_job_title = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ReachOutRCAQuotation', 'quotee_job_title'))

    panels = [
        FieldPanel('quotation'),
        FieldPanel('quotee'),
        FieldPanel('quotee_job_title')
    ]

class ReachOutRCAProject(Page, SocialFields):
    subtitle = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ReachOutRCAProject', 'subtitle'))
    year = models.CharField(max_length=4, blank=True, help_text=help_text('rca.ReachOutRCAProject', 'year'))
    description = RichTextField(help_text=help_text('rca.ReachOutRCAProject', 'description'))
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True, help_text=help_text('rca.ReachOutRCAProject', 'school'))
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True, help_text=help_text('rca.ReachOutRCAProject', 'programme'))
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ReachOutRCAProject', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.ReachOutRCAProject', 'show_on_homepage'))
    project = models.CharField(max_length=255, choices=REACHOUT_PROJECT_CHOICES, help_text=help_text('rca.ReachOutRCAProject', 'project'))
    random_order = models.IntegerField(null=True, blank=True, editable=False)
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ReachOutRCAProject', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('subtitle'),
        index.SearchField('get_research_type_display'),
        index.SearchField('description'),
        index.SearchField('get_school_display'),
        index.SearchField('get_programme_display'),
        index.SearchField('get_project_display'),
    )

    search_name = 'ReachOutRCA Project'

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        # Get related research
        projects = ReachOutRCAProject.objects.filter(live=True).order_by('random_order')
        projects = projects.filter(project=self.project)
        if self.programme:
            projects = projects.filter(programme__in=get_programme_synonyms(self.programme))
        elif self.school:
            projects = projects.filter(school=self.school)

        paginator = Paginator(projects, 4)

        page = request.GET.get('page')
        try:
            projects = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            projects = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            projects = paginator.page(paginator.num_pages)

        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, "rca/includes/innovation_rca_listing.html", {
                'self': self,
                'projects': projects
            })
        else:
            return render(request, self.template, {
                'self': self,
                'projects': projects
            })

    def get_related_news(self, count=4):
        return NewsItem.get_related(
            areas=['research'],
            programmes=get_programme_synonyms(self.programme) if self.programme else None,
            schools=([self.school] if self.school else None),
            count=count,
        )

    class Meta:
        verbose_name = "ReachOutRCA Project"

ReachOutRCAProject.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('subtitle'),
    InlinePanel('carousel_items', label="Carousel content"),
    FieldPanel('project'),
    InlinePanel('leader', label="Project leaders"),
    InlinePanel('assistant', label="Project assistants"),
    InlinePanel('themes', label="Project themes"),
    InlinePanel('participants', label="Project participants"),
    InlinePanel('partnerships', label="Project partnerships"),
    FieldPanel('description', classname="full"),
    FieldPanel('year'),
    FieldPanel('school'),
    FieldPanel('programme'),
    InlinePanel('links', label="Links"),
    InlinePanel('quotations', label="Middle column quotations"),
    FieldPanel('twitter_feed'),
]

ReachOutRCAProject.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('show_on_homepage'),
        ImageChooserPanel('feed_image'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]

# == ReachOut RCA Index page ==

class ReachOutRCAIndexAd(Orderable):
    page = ParentalKey('rca.ReachOutRCAIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.ReachOutRCAIndexAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class ReachOutRCAIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.ReachOutRCAIndex', 'intro'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ReachOutRCAIndex', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ReachOutRCAIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    indexed = False

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        # Get list of live projects
        projects = ReachOutRCAProject.objects.filter(live=True).order_by('random_order')

        # Apply filters
        project = request.GET.get('project', None)
        participant = request.GET.get('participant', None)
        theme = request.GET.get('theme', None)
        partnership = request.GET.get('partnership', None)

        # Run filters
        projects, filters = run_filters(projects, [
            ('project', 'project', project),
            ('participant', 'participants__participant', participant),
            ('theme', 'themes__theme', theme),
            ('partnership', 'partnerships__partnership', partnership),
        ])

        #pagination

        page = request.GET.get('page')
        paginator = Paginator(projects, 8)
        try:
            staff_pages = paginator.page(page)
        except PageNotAnInteger:
            staff_pages = paginator.page(1)
        except EmptyPage:
            staff_pages = paginator.page(paginator.num_pages)

        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, "rca/includes/reach_out_rca_listing.html", {
                'self': self,
                'projects': projects,
                'filters': json.dumps(filters),
            })
        else:
            return render(request, self.template, {
                'self': self,
                'projects': projects,
                'filters': json.dumps(filters),
            })

    class Meta:
        verbose_name = "ReachOutRCA Project Index"

ReachOutRCAIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel('manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
]

ReachOutRCAIndex.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]

# == Stream page ==


class StreamPageRelatedLink(Orderable, RelatedLinkMixin):
    page = ParentalKey('rca.StreamPage', related_name='related_links')

class StreamPageAd(Orderable):
    page = ParentalKey('rca.StreamPage', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.StreamPageAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class StreamPage(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.StreamPage', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.StreamPage', 'body'))
    poster_image = models.ForeignKey(
        'rca.RcaImage',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.StreamPage', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.StreamPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
        index.SearchField('body'),
    )

StreamPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    ImageChooserPanel('poster_image'),
    InlinePanel('related_links', label="Related links"),
    InlinePanel('manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
    ]

StreamPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        ImageChooserPanel('feed_image'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]
