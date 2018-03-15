from datetime import date
import datetime
import logging
import random

from itertools import chain

from captcha.fields import ReCaptchaField
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.signals import user_logged_in
from django.db import models
from django.db.models.signals import pre_delete
from django.core.serializers.json import DjangoJSONEncoder

from django.dispatch.dispatcher import receiver
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.views.decorators.vary import vary_on_headers
from wagtail.contrib.settings.models import BaseSetting
from wagtail.contrib.settings.registry import register_setting

from wagtail.wagtailcore.models import Page, Orderable, PageManager
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
from wagtail.wagtailcore.query import PageQuerySet
from wagtail.wagtailforms.models import AbstractFormField, FormSubmission
from wagtail.wagtailadmin.utils import send_mail

from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.models import ClusterableModel
from taggit.models import TaggedItemBase, Tag

from donations.forms import DonationForm
from donations.mail_admins import mail_exception, full_exc_info
import stripe

import hashlib

from rca.standard_stream_page.models import StandardStreamPage
from rca.utils.models import (
    RelatedLinkMixin, SocialFields, SidebarBehaviourFields,
    OptionalBlockFields, CarouselItemFields,
)
from rca_ee.models import FormPage
from taxonomy.models import Area, School, Programme

from rca.filters import run_filters, run_filters_q, combine_filters, get_filters_q
import json

from wagtailcaptcha.models import WagtailCaptchaEmailForm, WagtailCaptchaFormBuilder

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

    search_fields = AbstractImage.search_fields + [
        index.SearchField('creator'),
        index.SearchField('photographer'),
    ]

    api_fields = [
        'alt',
        'creator',
        'year',
        'focal_point_x',
        'focal_point_y',
        'focal_point_width',
        'focal_point_height',
    ]

    @property
    def default_alt_text(self):
        return self.alt

    @property
    def creator_and_year(self):
        return u" ".join([
            part for part in [
                self.creator,
                self.year,
            ]
            if part
        ])

    def caption_lines(self):
        if self.creator or self.year:
            first_line = u"%s, %s" % (self.title, self.creator_and_year)
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

        if self.creator or self.year:
            lines[0] = mark_safe(u"<i>%s</i>, %s" % (conditional_escape(self.title), conditional_escape(self.creator_and_year)))
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
    ('2016/17', (
        ('accessories', 'Accessories'),
        ('footwear', 'Footwear'),
        ('knitwear', 'Knitwear'),
        ('millinery', 'Millinery'),
        ('knit', 'Knit'),
        ('mixed-media', 'Mixed-media'),
        ('print', 'Print'),
        ('weave', 'Weave'),
        ('critical-Practice', 'Critical Practice'),
        ('performance', 'Performance'),
        ('public-sphere', 'Public Sphere'),
        ('moving-image', 'Moving Image'),
    )),
    ('2015/16', (
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
        ('knitwear', 'Knitwear'),
        ('footwear', 'Footwear'),
        ('accessory-design', 'Accessory Design'),
        ('millinery', 'Millinery'),
        ('design-as-catalyst-platform', 'Design as Catalyst Platform'),
        ('design-through-making-platform', 'Design through Making Platform'),
        ('design-for-manufacture-platform', 'Design for Manufacture Platform'),
        ('object-mediated-interactions-platform', 'Object Mediated Interactions Platform'),
        ('exploring-emergent-futures-platform', 'Exploring Emergent Futures Platform'),
    )),
    ('2014/15', (
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
    )),
)

SUSTAINRCA_CATEGORY_CHOICES = (
    ('solutionsforsociety', 'Solutions for Society'),
    ('inspiredproducts', 'Inspired Products'),
    ('visionaryprocess', 'Visionary Process'),
    ('movingminds', 'Moving Minds')
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


# == Snippet: Advert ==

class Advert(models.Model):
    page = models.ForeignKey(Page, related_name='adverts', null=True, blank=True, help_text=help_text('rca.Advert', 'page'))
    url = models.URLField(null=True, blank=True, help_text=help_text('rca.Advert', 'url'))
    text = models.CharField(max_length=255, help_text=help_text('rca.Advert', 'text', default="bold text"))
    plain_text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.Advert', 'plain_text'))
    show_globally = models.BooleanField(default=False, help_text=help_text('rca.Advert', 'show_globally'))
    promoted = models.BooleanField(blank=True, default=False, help_text=help_text('rca.Advert', 'promoted'))

    panels = [
        PageChooserPanel('page'),
        FieldPanel('url'),
        FieldPanel('text'),
        FieldPanel('plain_text'),
        FieldPanel('show_globally'),
        FieldPanel('promoted'),
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

class CustomContentModule(ClusterableModel):
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

class ContactSnippet(ClusterableModel):
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

class SchoolPageContactSnippet(Orderable):
    page = ParentalKey('rca.SchoolPage', related_name='contact_snippets')
    contact_snippet = models.ForeignKey('rca.ContactSnippet', related_name='+', help_text=help_text('rca.SchoolPageContactSnippet', 'contact_snippet'))

    panels = [
        SnippetChooserPanel('contact_snippet'),
    ]

class SchoolPageRelatedLink(Orderable, RelatedLinkMixin):
    page = ParentalKey('rca.SchoolPage', related_name='related_links')

class SchoolPageAd(Orderable):
    page = ParentalKey('rca.SchoolPage', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.SchoolPageAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad'),
    ]

class SchoolPageFeaturedContent(Orderable):
    page = ParentalKey('rca.SchoolPage', related_name='featured_content')
    content = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='+', help_text=help_text('rca.SchoolPage', 'featured_content'))

    panels = [
        PageChooserPanel('content'),
    ]


class SchoolPageResearchLinks(Orderable, RelatedLinkMixin):
    page = ParentalKey('rca.SchoolPage', related_name='research_link')


class SchoolPageAlsoOfInterest(Orderable, RelatedLinkMixin):
    page = ParentalKey('rca.SchoolPage', related_name='also_of_interest')


class SchoolPage(Page, SocialFields, SidebarBehaviourFields):
    PACKERY_CHOICES = zip(range(11), range(11))

    school = models.ForeignKey('taxonomy.School', null=True, on_delete=models.SET_NULL, related_name='school_pages', help_text=help_text('rca.SchoolPage', 'school'))
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.SchoolPage', 'background_image', default="The full bleed image in the background"))

    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.SchoolPage', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))

    video_url = models.URLField(null=True, blank=True, help_text=help_text('rca.SchoolPage', 'video_url'))
    school_brochure = models.ForeignKey('wagtaildocs.Document', null=True, blank=True, related_name='+', on_delete=models.SET_NULL, help_text=help_text('rca.SchoolPage', 'school_brochure', default="Link to the school brochure document"))


    packery_news = models.IntegerField("Number of news items to show", null=True, blank=True, choices=PACKERY_CHOICES, help_text=help_text('rca.SchoolPage', 'packery_news'))
    packery_events = models.IntegerField("Number of events to show (excluding RCA Talks)", null=True, blank=True, choices=PACKERY_CHOICES, help_text=help_text('rca.SchoolPage', 'packery_events'))
    packery_events_rcatalks = models.IntegerField("Number of RCA Talk events to show", null=True, blank=True, choices=PACKERY_CHOICES, help_text=help_text('rca.SchoolPage', 'packery_events_rcatalks'))
    packery_blog = models.IntegerField("Number of blog items to show", null=True, blank=True, choices=PACKERY_CHOICES, help_text=help_text('rca.SchoolPage', 'packery_blog'))
    packery_standard_pages = models.IntegerField("Number of standard pages to show", null=True, blank=True, choices=PACKERY_CHOICES, help_text=help_text('rca.SchoolPage', 'packery_standard_pages'))
    packery_lightbox_galleries = models.IntegerField("Number of lightbox galleries to show", null=True, blank=True, choices=PACKERY_CHOICES, help_text=help_text('rca.SchoolPage', 'packery_research'))
    packery_research = models.IntegerField("Number of research items to show", null=True, blank=True, choices=PACKERY_CHOICES, help_text=help_text('rca.SchoolPage', 'packery_research'))

    ## old content, do not know whether this will be needed
    head_of_school = models.ForeignKey('rca.StaffPage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.SchoolPage', 'head_of_school'))
    head_of_school_statement = RichTextField(help_text=help_text('rca.SchoolPage', 'head_of_school_statement'), null=True, blank=True)
    head_of_school_link = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.SchoolPage', 'head_of_school_link'))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.SchoolPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + [
        index.RelatedFields('school', [
            index.SearchField('display_name'),
        ]),
    ]

    search_name = 'School'

    @vary_on_headers('X-Requested-With')
    def serve(self, request, show_draft_pathways=False):
        exclude = []
        if request.GET.get('exclude'):
            for extra_exclude in request.GET.get('exclude', '').split(','):
                try:
                    exclude.append(int(extra_exclude))
                except (TypeError, ValueError):
                    pass

        featured_ids = self.featured_content.all().values_list('content_id', flat=True)


        # packery selection
        news = NewsItem.objects\
            .filter(live=True, related_schools__school=self.school)\
            .exclude(id__in=featured_ids) \
            .order_by('-date')
        events = EventItem.past_objects\
            .filter(live=True, related_schools__school=self.school)\
            .exclude(id__in=featured_ids) \
            .exclude(audience='rcatalks') \
            .extra(select={
                'latest_date': "SELECT GREATEST(date_from, date_to) AS latest_date FROM rca_eventitemdatestimes where rca_eventitemdatestimes.page_id = wagtailcore_page.id ORDER BY latest_date DESC LIMIT 1",
            })\
            .order_by('-latest_date')
        events_rcatalks = EventItem.past_objects\
            .filter(live=True, related_schools__school=self.school, audience='rcatalks')\
            .exclude(id__in=featured_ids) \
            .extra(select={
                'is_rca_talk': True,
                'latest_date': "SELECT GREATEST(date_from, date_to) AS latest_date FROM rca_eventitemdatestimes where rca_eventitemdatestimes.page_id = wagtailcore_page.id ORDER BY latest_date DESC LIMIT 1",
            })\
            .order_by('-latest_date')
        blog = RcaBlogPage.objects\
            .filter(live=True, school=self.school)\
            .exclude(id__in=featured_ids) \
            .order_by('-date')
        standard_pages = StandardPage.objects \
            .filter(live=True, show_on_school_page=True, related_school=self.school) \
            .exclude(tags__name__iexact=StandardPage.STUDENT_STORY_TAG)\
            .exclude(tags__name__iexact=StandardPage.ALUMNI_STORY_TAG)\
            .exclude(id__in=featured_ids) \
            .order_by('-latest_revision_created_at')
        lightboxes = LightboxGalleryPage.objects \
            .filter(live=True, show_on_school_page=True, related_schools__school=self.school) \
            .exclude(id__in=featured_ids) \
            .order_by('-latest_revision_created_at')
        research = ResearchItem.objects.live() \
            .filter(featured=True, school=self.school) \
            .exclude(id__in=featured_ids) \
            .order_by('-latest_revision_created_at')

        # Get all kinds of student stories
        student_stories_standard = StandardPage.objects\
            .filter(show_on_school_page=True, tags__name__iexact=StandardPage.STUDENT_STORY_TAG)\
            .exclude(tags__name__iexact=StandardPage.ALUMNI_STORY_TAG)\
            .values_list('pk', flat=True)
        student_stories_standard_stream = StandardStreamPage.objects\
            .filter(show_on_school_page=True, tags__name__iexact=StandardStreamPage.STUDENT_STORY_TAG)\
            .exclude(tags__name__iexact=StandardStreamPage.ALUMNI_STORY_TAG)\
            .values_list('pk', flat=True)

        student_stories = Page.objects.live()\
            .filter(models.Q(pk__in=student_stories_standard_stream) | models.Q(pk__in=student_stories_standard))\
            .exclude(pk__in=featured_ids) \
            .annotate(is_student_story=models.Value(True, output_field=models.BooleanField())) \
            .order_by('?')

        # Get all kinds of alumni stories
        alumni_stories_standard = StandardPage.objects\
            .filter(show_on_school_page=True, tags__name__iexact=StandardPage.ALUMNI_STORY_TAG)\

        alumni_stories_standard_stream = StandardStreamPage.objects\
            .filter(show_on_school_page=True, tags__name__iexact=StandardStreamPage.ALUMNI_STORY_TAG)\

        alumni_stories = Page.objects.live()\
            .filter(models.Q(pk__in=alumni_stories_standard) | models.Q(pk__in=alumni_stories_standard_stream))\
            .exclude(pk__in=featured_ids) \
            .annotate(is_alumni_story=models.Value(True, output_field=models.BooleanField()))\
            .order_by('?')

        if exclude:
            news = news.exclude(id__in=exclude)
            events = events.exclude(id__in=exclude)
            events_rcatalks = events_rcatalks.exclude(id__in=exclude)
            blog = blog.exclude(id__in=exclude)
            standard_pages = standard_pages.exclude(id__in=exclude)
            lightboxes = lightboxes.exclude(id__in=exclude)
            research = research.exclude(id__in=exclude)

        packery = list(chain(
            news[:self.packery_news],
            events[:self.packery_events],
            events_rcatalks[:self.packery_events_rcatalks],
            blog[:self.packery_blog],
            standard_pages[:self.packery_standard_pages],
            student_stories[:self.packery_standard_pages],
            alumni_stories[:self.packery_standard_pages],
            lightboxes[:self.packery_lightbox_galleries],
            research[:self.packery_research],
        ))

        random.shuffle(packery)

        if request.is_ajax():
            return render(request, "rca/includes/school_page_packery.html", {
                'self': self,
                'packery': packery
            })
        else:
            return render(request, self.template, {
                'self': self,
                'packery': packery
            })

    @property
    def preview_modes(self):
        return super(SchoolPage, self).preview_modes + [
            ('show_draft_pathways', 'Show draft pathways')
        ]

    def serve_preview(self, request, mode_name):
        if mode_name == 'show_draft_pathways':
            return self.serve(request, show_draft_pathways=True)
        return super(SchoolPage, self).serve_preview(request, mode_name)


SchoolPage.content_panels = [
    FieldPanel('title', classname="full title"),
    ImageChooserPanel('background_image'),

    InlinePanel('research_link', label="Research"),

    MultiFieldPanel([
        PageChooserPanel('head_of_school', 'rca.StaffPage'),
        PageChooserPanel('head_of_school_link'),
        FieldPanel('video_url'),
        DocumentChooserPanel('school_brochure'),
    ], 'About the school'),
    MultiFieldPanel([
        FieldPanel('packery_news'),
        FieldPanel('packery_events'),
        FieldPanel('packery_events_rcatalks'),
        FieldPanel('packery_blog'),
        FieldPanel('packery_standard_pages'),
        FieldPanel('packery_lightbox_galleries'),
        FieldPanel('packery_research'),
    ], 'Packery content'),
    InlinePanel('contact_snippets', label="Contacts"),
    InlinePanel('featured_content', label="Featured content"),
    InlinePanel('also_of_interest', label="Also of interest"),
    InlinePanel('related_links', label="Related links"),

    # InlinePanel('carousel_items', label="Carousel content", help_text="test"),
    # PageChooserPanel('head_of_school', 'rca.StaffPage'),
    # FieldPanel('head_of_school_statement', classname="full"),
    # PageChooserPanel('head_of_school_link'),
    # FieldPanel('twitter_feed'),
    # PageChooserPanel('head_of_research', 'rca.StaffPage'),
    # FieldPanel('head_of_research_statement', classname="full"),
    # PageChooserPanel('head_of_research_link'),
    # InlinePanel('manual_adverts', label="Manual adverts"),
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

class ProgrammePageRelatedLink(Orderable, RelatedLinkMixin):
    page = ParentalKey('rca.ProgrammePage', related_name='related_links')

class ProgrammePageHowToApply(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='how_to_apply')
    link = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='+', help_text=help_text('rca.ProgrammePageHowToApply', 'link'))
    link_text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ProgrammePageHowToApply', 'link_text'))

    panels = [
        PageChooserPanel('link'),
        FieldPanel('link_text')
    ]

class ProgrammePageKeyDetails(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='key_details')
    text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ProgrammePageKeyDetails', 'text'))

    panels = [
        FieldPanel('text')
    ]

class ProgrammePageKeyContent(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='key_content')
    link = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='+', help_text=help_text('rca.ProgrammePageKeyContent', 'link'))
    link_text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ProgrammePageKeyContent', 'link_text'))

    panels = [
        PageChooserPanel('link'),
        FieldPanel('link_text')
    ]

class ProgrammePageFindOutMore(Orderable, RelatedLinkMixin):
    page = ParentalKey('rca.ProgrammePage', related_name='find_out_more')


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


class ProgrammePageProgramme(models.Model):
    page = ParentalKey('rca.ProgrammePage', related_name='programmes')
    programme = models.ForeignKey('taxonomy.Programme', null=True, on_delete=models.SET_NULL, related_name='programme_pages', help_text=help_text('rca.ProgrammePageProgramme', 'programme'))

    panels = [FieldPanel('programme')]

class ProgrammePageContactSnippet(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='contact_snippets')
    contact_snippet = models.ForeignKey('rca.ContactSnippet', related_name='+', help_text=help_text('rca.ProgrammePageContactSnippet', 'contact_snippet'))

    panels = [
        SnippetChooserPanel('contact_snippet'),
    ]

class ProgrammePageAd(Orderable):
    page = ParentalKey('rca.ProgrammePage', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.ProgrammePageAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad'),
    ]

class ProgrammePage(Page, SocialFields, SidebarBehaviourFields):
    school = models.ForeignKey('taxonomy.School', null=True, on_delete=models.SET_NULL, related_name='programme_pages', help_text=help_text('rca.ProgrammePage', 'school'))
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ProgrammePage', 'background_image', default="The full bleed image in the background"))
    head_of_programme = models.ForeignKey('rca.StaffPage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ProgrammePage', 'head_of_programme', default="Select the profile page of the head of this programme."))
    head_of_programme_second = models.ForeignKey('rca.StaffPage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', verbose_name="Second head of programme", help_text=help_text('rca.ProgrammePage', 'head_of_programme_secondary', default="Select the profile page of another head of this programme."))
    head_of_programme_statement = RichTextField("Head(s) of programme statement", null=True, blank=True, help_text=help_text('rca.ProgrammePage', 'head_of_programme_statement'))
    head_of_programme_link = models.ForeignKey(Page, verbose_name="Head(s) of programme link", null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ProgrammePage', 'head_of_programme_link', default="The link to the Head(s) of Programme Welcome Page"))
    programme_specification_document = models.ForeignKey('wagtaildocs.Document', null=True, blank=True, related_name='+', on_delete=models.SET_NULL, help_text=help_text('rca.ProgrammePage', 'programme_specification', default="Download the programme specification"))
    ma_programme_description_link = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ProgrammePage', 'ma_programme_description_link'))
    ma_programme_description_link_text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ProgrammePage', 'ma_programme_description_link_text'))

    ma_programme_staff_link = models.URLField("Programme staff link", blank=True, help_text=help_text('rca.ProgrammePage', 'ma_programme_staff_link'))
    ma_programme_staff_link_text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ProgrammePage', 'ma_programme_staff_link_text'))
    ma_programme_overview_link = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ProgrammePage', 'ma_programme_overview_link'))
    ma_programme_overview_link_text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ProgrammePage', 'ma_entry_requirements_link_text'))

    ma_entry_requirements_link = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ProgrammePage', 'ma_entry_requirements_link'))
    ma_entry_requirements_link_text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ProgrammePage', 'ma_programme_overview_link_text'))
    facilities_link = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ProgrammePage', 'facilities_link'))
    facilities_link_text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ProgrammePage', 'facilities_link_text'))
    graduate_destinations_link = models.ForeignKey(Page, null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ProgrammePage', 'graduate_destinations_link'))
    graduate_destinations_link_text = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ProgrammePage', 'graduate_destinations_link_text'))
    key_content_header = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ProgrammePage', 'key_content_header'))
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ProgrammePage', 'twitter_feed', default="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term"))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ProgrammePage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))


    search_fields = Page.search_fields + [
        index.SearchField('get_programme_display'),
        index.RelatedFields('school', [
            index.SearchField('display_name'),
        ]),
    ]

    search_name = 'Programme'

    def get_school_url(self):
        try:
            return SchoolPage.objects.get(school=self.school).url
        except SchoolPage.DoesNotExist:
            return ""

    def get_programme_display(self):
        programmes = Programme.objects.filter(
            id__in=self.programmes.all().values_list('programme_id', flat=True)
        )

        return ", ".join([p.display_name for p in programmes])

    def pathways(self):
        return self.get_children().live().type(PathwayPage).specific()

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        programmes = [p.programme for p in self.programmes.all()]
        research_items = ResearchItem.objects.filter(live=True, programme__in=programmes, featured=True).order_by('random_order')

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
    MultiFieldPanel([
        PageChooserPanel('head_of_programme', 'rca.StaffPage',),
        PageChooserPanel('head_of_programme_second', 'rca.StaffPage',),
        FieldPanel('head_of_programme_statement', classname="full"),
        PageChooserPanel('head_of_programme_link'),
    ], 'Head of programme introduction'),
    MultiFieldPanel([
        DocumentChooserPanel('programme_specification_document'),
        InlinePanel('key_details', label="Key details"),
        InlinePanel('contact_snippets', label="Contacts"),
    ], 'Key programme information'),
    MultiFieldPanel([
        PageChooserPanel('ma_programme_description_link'),
        FieldPanel('ma_programme_description_link_text'),
    ], 'MA programme description'),
    MultiFieldPanel([
        PageChooserPanel('ma_programme_overview_link'),
        FieldPanel('ma_programme_overview_link_text'),
    ], 'MA programme overview'),
    MultiFieldPanel([
        PageChooserPanel('ma_entry_requirements_link'),
        FieldPanel('ma_entry_requirements_link_text'),
    ], 'MA Entry requirements'),
    MultiFieldPanel([
        FieldPanel('ma_programme_staff_link'),
        FieldPanel('ma_programme_staff_link_text'),
    ], 'MA programme staff'),
    MultiFieldPanel([
        PageChooserPanel('facilities_link'),
        FieldPanel('facilities_link_text'),
    ], 'Facilities'),
    MultiFieldPanel([
        InlinePanel('how_to_apply', label="How to apply"),
    ], 'How to apply'),
    MultiFieldPanel([
        PageChooserPanel('graduate_destinations_link'),
        FieldPanel('graduate_destinations_link_text'),
    ], 'Graduate destinations'),
    MultiFieldPanel([
        FieldPanel('key_content_header'),
        InlinePanel('key_content', label="Other key content links"),
    ], 'Other key content'),
    FieldPanel('twitter_feed'),
    InlinePanel('find_out_more', label="Find out more"),
    InlinePanel('our_sites', label="Our sites"),
    InlinePanel('related_links', label="Related links"),
    InlinePanel('manual_adverts', label="Manual adverts"),
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

    InlinePanel('programmes', min_num=1, label="Programmes (*at least one is required)"),
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
        SnippetChooserPanel('ad'),
    ]

class NewsIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.NewsIndex', 'intro'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewsIndex', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.NewsIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))
    subpage_types = ['NewsItem']

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

    search_name = None

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        programme_slug = request.GET.get('programme')
        school_slug = request.GET.get('school')
        area_slug = request.GET.get('area')

        # Programme
        programme_options = Programme.objects.filter(
            id__in=NewsItemRelatedProgramme.objects.values_list('programme', flat=True)
        )
        programme = programme_options.filter(slug=programme_slug).first()

         # School
        school_options = School.objects.filter(
            id__in=NewsItemRelatedSchool.objects.values_list('school', flat=True)
        ) | School.objects.filter(
            id__in=NewsItemRelatedProgramme.objects.values_list('programme__school', flat=True)
        )
        school = school_options.filter(slug=school_slug).first()

        if school:
            # Filter programme options to only this school
            programme_options = programme_options.filter(school=school)

            # Prevent programme from a different school being selected
            if programme and programme.school != school:
                programme = None

        # Area
        area_options = Area.objects.filter(
            id__in=NewsItemArea.objects.values_list('area', flat=True)
        )
        area = area_options.filter(slug=area_slug).first()

        # Get news items
        news_items = NewsItem.objects.live().descendant_of(self).filter(show_on_news_index=True)

        if programme:
            news_items = news_items.filter(related_programmes__programme=programme)
        elif school:
            news_items = news_items.filter(
                models.Q(related_schools__school=school) |
                models.Q(related_programmes__programme__school=school)
            )

        if area:
            news_items = news_items.filter(models.Q(areas__area=area))

        news_items = news_items.distinct().order_by('-date')

        # Pagination
        page = request.GET.get('page')
        paginator = Paginator(news_items, 10)  # Show 10 news items per page
        try:
            news_items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            news_items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver lst page of results.
            news_items = paginator.page(paginator.num_pages)

        filters = [{
            "name": "school",
            "current_value": school.slug if school else None,
            "options": [""] + list(school_options.values_list('slug', flat=True)),
        }, {
            "name": "programme",
            "current_value": programme.slug if programme else None,
            "options": [""] + list(programme_options.values_list('slug', flat=True)),
        }, {
            "name": "areas",
            "current_value": area.slug if area else None,
            "options": [""] + list(area_options.values_list('slug', flat=True)),
        }]

        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, "rca/includes/news_listing.html", {
                'self': self,
                'news': news_items,
                'filters': json.dumps(filters),
            })
        else:
            return render(request, self.template, {
                'self': self,
                'news': news_items,
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

    api_fields = [
        'link',
        'link_text',
    ]

    panels=[
        FieldPanel('link'),
        FieldPanel('link_text')
    ]

class NewsItemRelatedSchool(models.Model):
    page = ParentalKey('rca.NewsItem', related_name='related_schools')
    school = models.ForeignKey('taxonomy.School', null=True, on_delete=models.SET_NULL, related_name='news_items', help_text=help_text('rca.NewsItemRelatedSchool', 'school'))

    api_fields = [
        'school',
    ]

    panels = [
        FieldPanel('school')
    ]

class NewsItemRelatedProgramme(models.Model):
    page = ParentalKey('rca.NewsItem', related_name='related_programmes')
    programme = models.ForeignKey('taxonomy.Programme', null=True, on_delete=models.SET_NULL, related_name='news_items', help_text=help_text('rca.NewsItemRelatedProgramme', 'programme'))

    api_fields = [
        'programme',
    ]

    panels = [FieldPanel('programme')]

class NewsItemArea(models.Model):
    page = ParentalKey('rca.NewsItem', related_name='areas')
    area = models.ForeignKey('taxonomy.Area', null=True, on_delete=models.SET_NULL, related_name='news_items', help_text=help_text('rca.NewsItemArea', 'area'))

    api_fields = [
        'area',
    ]

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

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    api_fields = [
        'author',
        'date',
        'intro',
        'body',
        'listing_intro',
        'feed_image',
        'carousel_items',
        'related_links',
        'related_schools',
        'related_programmes',
        'areas',
    ]

    pushable_to_intranet = True

    search_name = 'News'

    def get_related_news(self, count=4):
        return NewsItem.get_related(
            areas=Area.objects.filter(id__in=self.areas.values_list('area_id', flat=True)),
            programmes=Programme.objects.filter(id__in=self.related_programmes.values_list('programme_id', flat=True)),
            schools=School.objects.filter(id__in=self.related_schools.values_list('school_id', flat=True)),
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
        area_ids = [0]
        if areas is not None:
            area_ids = list(areas.values_list('id', flat=True)) or [0]

        programme_ids = [0]
        if programmes is not None:
            programme_ids = list(programmes.values_list('id', flat=True)) or [0]

        school_ids = [0]
        if schools is not None:
            school_ids = list(schools.values_list('id', flat=True)) or [0]

        results = NewsItem.objects.extra(
            select={'score': """
                (
                    SELECT COUNT(*) FROM rca_newsitemarea
                    WHERE rca_newsitemarea.page_id=wagtailcore_page.id
                        AND rca_newsitemarea.area_id IN %s
                ) * 100
                + (
                    SELECT COUNT(*) FROM rca_newsitemrelatedprogramme
                    WHERE rca_newsitemrelatedprogramme.page_id=wagtailcore_page.id
                        AND rca_newsitemrelatedprogramme.programme_id IN %s
                ) * 10
                + (
                    SELECT COUNT(*) FROM rca_newsitemrelatedschool
                    WHERE rca_newsitemrelatedschool.page_id=wagtailcore_page.id
                        AND rca_newsitemrelatedschool.school_id IN %s
                ) * 1
            """},
            select_params=(tuple(area_ids), tuple(programme_ids), tuple(school_ids))
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
        SnippetChooserPanel('ad'),
    ]

class PressReleaseIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.PressReleaseIndex', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.PressReleaseIndex', 'body'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.PressReleaseIndex', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.PressReleaseIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

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
    school = models.ForeignKey('taxonomy.School', null=True, on_delete=models.SET_NULL, related_name='press_releases', help_text=help_text('rca.PressReleaseRelatedSchool', 'school'))

    panels = [
        FieldPanel('school')
    ]

class PressReleaseRelatedProgramme(models.Model):
    page = ParentalKey('rca.PressRelease', related_name='related_programmes')
    programme = models.ForeignKey('taxonomy.Programme', null=True, on_delete=models.SET_NULL, related_name='press_releases', help_text=help_text('rca.PressReleaseRelatedProgramme', 'programme'))

    panels = [FieldPanel('programme')]

class PressReleaseArea(models.Model):
    page = ParentalKey('rca.PressRelease', related_name='areas')
    area = models.ForeignKey('taxonomy.Area', null=True, on_delete=models.SET_NULL, related_name='press_releases', help_text=help_text('rca.PressReleaseArea', 'area'))

    panels = [FieldPanel('area')]

class PressRelease(Page, SocialFields):
    author = models.CharField(max_length=255, help_text=help_text('rca.PressRelease', 'author'))
    date = models.DateField(help_text=help_text('rca.PressRelease', 'date'))
    intro = RichTextField(help_text=help_text('rca.PressRelease', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.PressRelease', 'body'))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.PressRelease', 'show_on_homepage'))
    listing_intro = models.CharField(max_length=100, blank=True, help_text=help_text('rca.PressRelease', 'listing_intro', default="Used only on pages listing news items"))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.PressRelease', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

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

    api_fields = [
        'image',
        'name',
        'surname',
        'link_page',
        'link',
    ]

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
    school = models.ForeignKey('taxonomy.School', null=True, on_delete=models.SET_NULL, related_name='event_items', help_text=help_text('rca.EventItemRelatedSchool', 'school'))

    api_fields = [
        'school',
    ]

    panels = [FieldPanel('school')]

class EventItemRelatedProgramme(models.Model):
    page = ParentalKey('rca.EventItem', related_name='related_programmes')
    programme = models.ForeignKey('taxonomy.Programme', null=True, on_delete=models.SET_NULL, related_name='event_items', help_text=help_text('rca.EventItemRelatedProgramme', 'programme'))

    api_fields = [
        'programme',
    ]

    panels = [FieldPanel('programme')]

class EventItemRelatedArea(models.Model):
    page = ParentalKey('rca.EventItem', related_name='related_areas')
    area = models.ForeignKey('taxonomy.Area', null=True, on_delete=models.SET_NULL, related_name='event_items', help_text=help_text('rca.EventItemRelatedArea', 'area'))

    api_fields = [
        'area',
    ]

    panels = [FieldPanel('area')]

class EventItemContactPhone(Orderable):
    page = ParentalKey('rca.EventItem', related_name='contact_phone')
    phone_number = models.CharField(max_length=255, help_text=help_text('rca.EventItemContactPhone', 'phone_number'))

    api_fields = [
        'phone_number',
    ]

    panels = [
        FieldPanel('phone_number')
    ]

class EventItemContactEmail(Orderable):
    page = ParentalKey('rca.EventItem', related_name='contact_email')
    email_address = models.CharField(max_length=255, help_text=help_text('rca.EventItemContactEmail', 'email_address'))

    api_fields = [
        'email_address',
    ]

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

    api_fields = [
        'date_from',
        'date_to',
        'time_from',
        'time_to',
        'time_other',
    ]

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

    api_fields = [
        'link',
        'text',
    ]

    panels = [
        FieldPanel('link'),
        FieldPanel('text'),
    ]

class FutureEventItemManager(PageManager):
    def get_queryset(self):
        return super(FutureEventItemManager, self).get_queryset().extra(
            where=["wagtailcore_page.id IN (SELECT DISTINCT page_id FROM rca_eventitemdatestimes WHERE date_from >= %s OR date_to >= %s)"],
            params=[date.today(), date.today()]
        )

class FutureNotCurrentEventItemManager(PageManager):
    def get_queryset(self):
        return super(FutureNotCurrentEventItemManager, self).get_queryset().extra(
            where=["wagtailcore_page.id IN (SELECT DISTINCT page_id FROM rca_eventitemdatestimes WHERE date_from >= %s)"],
            params=[date.today()]
        ).extra(
            select={'next_date_from': '(SELECT date_from FROM rca_eventitemdatestimes WHERE page_id=wagtailcore_page.id AND date_from >= %s LIMIT 1)'},
            select_params=[date.today()],
            order_by=['next_date_from']
        )

class PastEventItemManager(PageManager):
    def get_queryset(self):
        return super(PastEventItemManager, self).get_queryset().extra(
            where=["wagtailcore_page.id NOT IN (SELECT DISTINCT page_id FROM rca_eventitemdatestimes WHERE date_from >= %s OR date_to >= %s)"],
            params=[date.today(), date.today()]
        )

class EventItem(Page, SocialFields):
    body = RichTextField(help_text=help_text('rca.EventItem', 'body'))
    audience = models.CharField(max_length=255, choices=EVENT_AUDIENCE_CHOICES, help_text=help_text('rca.EventItem', 'audience'))
    area = models.ForeignKey('taxonomy.Area', null=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.EventItem', 'area'))
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

    objects = PageManager()
    future_objects = FutureEventItemManager()
    past_objects = PastEventItemManager()
    future_not_current_objects = FutureNotCurrentEventItemManager()

    search_fields = Page.search_fields + [
        index.SearchField('body'),
        index.SearchField('get_location_display'),
        index.SearchField('location_other'),
    ]

    api_fields = [
        'body',
        'audience',
        'location',
        'location_other',
        'specific_directions',
        'specific_directions_link',
        'gallery',
        'special_event',
        'cost',
        'eventbrite_id',
        'listing_intro',
        'middle_column_body',
        'contact_title',
        'contact_address',
        'contact_phone',
        'contact_email',
        'contact_link',
        'contact_link_text',
        'feed_image',
        'carousel_items',
        'related_schools',
        'related_programmes',
        'related_areas',
        'speakers',
        'dates_times',
        'external_links',
    ]

    pushable_to_intranet = True

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
        SnippetChooserPanel('ad'),
    ]

class EventIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.EventIndex', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.EventIndex', 'body'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.EventIndex', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.EventIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    search_name = None

    def future_events(self):
        return EventItem.future_objects.filter(live=True, path__startswith=self.path)

    def past_events(self):
        return EventItem.past_objects.filter(live=True, path__startswith=self.path)

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        programme_slug = request.GET.get('programme')
        school_slug = request.GET.get('school')
        location = request.GET.get('location')
        location_other = request.GET.get('location_other')
        area_slug = request.GET.get('area')
        audience = request.GET.get('audience')
        period = request.GET.get('period')

        # Programme
        programme_options = Programme.objects.filter(
            id__in=EventItemRelatedProgramme.objects.values_list('programme', flat=True)
        )
        programme = programme_options.filter(slug=programme_slug).first()

        # School
        school_options = School.objects.filter(
            id__in=EventItemRelatedSchool.objects.values_list('school', flat=True)
        ) | School.objects.filter(
            id__in=EventItemRelatedProgramme.objects.values_list('programme__school', flat=True)
        )
        school = school_options.filter(slug=school_slug).first()

        if school:
            # Filter programme options to only this school
            programme_options = programme_options.filter(school=school)

            # Prevent programme from a different school being selected
            if programme and programme.school != school:
                programme = None

         # Area
        area_options = Area.objects.filter(
            id__in=EventItemRelatedArea.objects.values_list('area', flat=True)
        )
        area = area_options.filter(slug=area_slug).first()

        # Get events
        if period == 'past':
            events = self.past_events()
        else:
            events = self.future_events()

        if programme:
            events = events.filter(related_programmes__programme=programme)
        elif school:
            events = events.filter(
                models.Q(related_schools__school=school) |
                models.Q(related_programmes__programme__school=school)
            )

        if area:
            events = events.filter(models.Q(related_areas__area=area))

        if location:
            events = events.filter(location=location)

        if audience:
            events = events.filter(audience=audience)

        events = events.annotate(start_date=models.Min('dates_times__date_from'), end_date=models.Max('dates_times__date_to'))
        if period== 'past':
            events = events.order_by('start_date').reverse()
        else:
            events = events.order_by('start_date')

        events = events.distinct()

        # Pagination
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

        filters = [{
            "name": "school",
            "current_value": school.slug if school else None,
            "options": [""] + list(school_options.values_list('slug', flat=True)),
        }, {
            "name": "programme",
            "current_value": programme.slug if programme else None,
            "options": [""] + list(programme_options.values_list('slug', flat=True)),
        }, {
            "name": "location",
            "current_value": location,
            "options": [""] + list(dict(EVENT_LOCATION_CHOICES).keys()),
        }, {
            "name": "area",
            "current_value": area.slug if area else None,
            "options": [""] + list(area_options.values_list('slug', flat=True)),
        }, {
            "name": "audience",
            "current_value": audience,
            "options": [""] + list(dict(EVENT_AUDIENCE_CHOICES).keys()),
        }]

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
        SnippetChooserPanel('ad'),
    ]

class TalksIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.TalksIndex', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.TalksIndex', 'body'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.TalksIndex', 'twitter_feed', default="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term"))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.TalksIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    search_page = None

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        talks = EventItem.past_objects.filter(live=True, audience='rcatalks').annotate(start_date=models.Min('dates_times__date_from')).order_by('-start_date')

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
        SnippetChooserPanel('ad'),
    ]

class ReviewsIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.ReviewsIndex', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.ReviewsIndex', 'body'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ReviewsIndex', 'twitter_feed', default="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term"))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ReviewsIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

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
        SnippetChooserPanel('ad'),
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

    search_fields = Page.search_fields + [
        index.SearchField('body'),
        index.SearchField('strapline'),
        index.SearchField('author'),
    ]

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
        SnippetChooserPanel('ad'),
    ]

class StandardPageReusableTextSnippet(Orderable):
    page = ParentalKey('rca.StandardPage', related_name='reusable_text_snippets')
    reusable_text_snippet = models.ForeignKey('rca.ReusableTextSnippet', related_name='+', help_text=help_text('rca.StandardPageReusableTextSnippet', 'reusable_text_snippet'))

    panels = [
        SnippetChooserPanel('reusable_text_snippet'),
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
    related_school = models.ForeignKey('taxonomy.School', null=True, blank=True, on_delete=models.SET_NULL, related_name='standard_pages', help_text=help_text('rca.StandardPage', 'related_school'))
    related_programme = models.ForeignKey('taxonomy.Programme', null=True, blank=True, on_delete=models.SET_NULL, related_name='standard_pages', help_text=help_text('rca.StandardPage', 'related_programme'))
    related_area = models.ForeignKey('taxonomy.Area', null=True, blank=True, on_delete=models.SET_NULL, related_name='standard_pages', help_text=help_text('rca.StandardPage', 'related_area'))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.StandardPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))
    tags = ClusterTaggableManager(through=StandardPageTag, help_text=help_text('rca.StandardPage', 'tags'), blank=True)

    show_on_school_page = models.BooleanField(default=False, help_text=help_text('rca.StandardPage', 'show_on_school_page'))

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    api_fields = [
        'intro',
        'body',
        'strapline',
        'twitter_feed',
        'related_school',
        'related_programme',
        'related_area',
        'feed_image',
        'tags',
        'carousel_items',
        'related_links',
        'quotations',
        'documents',
        'images',
    ]

    # StandardPages with a STUDENT_STORY_TAG or ALUMNI_STORY_TAG can be listed on the homepage packery separately.
    # TODO: This can be done more elegantly with proxy models. See related PR here: https://github.com/torchbox/wagtail/pull/1736/files
    STUDENT_STORY_TAG = 'student-story'
    ALUMNI_STORY_TAG = 'alumni-story'

    @property
    def search_name(self):
        if self.related_programme:
            return self.related_programme.display_name

        if self.related_school:
            return self.related_school.display_name

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
        FieldPanel('show_on_school_page'),
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
        FieldPanel('related_area'),
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
        SnippetChooserPanel('ad'),
    ]

class StandardIndexCustomContentModules(Orderable):
    page = ParentalKey('rca.StandardIndex', related_name='custom_content_modules')
    custom_content_module = models.ForeignKey('rca.CustomContentModule', related_name='+', help_text=help_text('rca.StandardIndexCustomContentModules', 'custom_content_module'))

    panels = [
        SnippetChooserPanel('custom_content_module'),
    ]

class StandardIndexContactSnippet(Orderable):
    page = ParentalKey('rca.StandardIndex', related_name='contact_snippets')
    contact_snippet = models.ForeignKey('rca.ContactSnippet', related_name='+', help_text=help_text('rca.StandardIndexContactSnippet', 'contact_snippet'))

    panels = [
        SnippetChooserPanel('contact_snippet'),
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
    news_carousel_area = models.ForeignKey('taxonomy.Area', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.StandardIndex', 'news_carousel_area'))
    staff_feed_source = models.ForeignKey('taxonomy.School', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.StandardIndex', 'staff_feed_source'))
    show_events_feed = models.BooleanField(default=False, help_text=help_text('rca.StandardIndex', 'show_events_feed'))
    events_feed_area = models.ForeignKey('taxonomy.Area', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.StandardIndex', 'events_feed_area'))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.StandardIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))
    hide_body = models.BooleanField(default=True, help_text=help_text('rca.StandardIndex', 'hide_body'))

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('strapline'),
        index.SearchField('body'),
    ]

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
        feed = list(chain(manual_feed, feed_source))

        if manual_feed or self.staff_feed_source:
            return feed

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        # Get list of events
        events = EventItem.future_objects.filter(live=True).annotate(start_date=models.Min('dates_times__date_from')).filter(area=self.events_feed_area).order_by('start_date')

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
        SnippetChooserPanel('ad'),
    ]

class HomePageRelatedLink(Orderable, RelatedLinkMixin):
    page = ParentalKey('rca.HomePage', related_name='related_links')

class HomePage(Page, SocialFields):
    PACKERY_CHOICES = zip(range(11), range(11))

    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.HomePage', 'background_image', default="The full bleed image in the background"))
    news_item_1 = models.ForeignKey('wagtailcore.Page', null=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.HomePage', 'news_item_1'))
    news_item_2 = models.ForeignKey('wagtailcore.Page', null=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.HomePage', 'news_item_2'))
    packery_news = models.IntegerField("Number of news items to show", null=True, blank=True, choices=PACKERY_CHOICES, help_text=help_text('rca.HomePage', 'packery_news'))
    packery_staff = models.IntegerField("Number of staff to show", null=True, blank=True, choices=PACKERY_CHOICES, help_text=help_text('rca.HomePage', 'packery_staff'))
    packery_tweets = models.IntegerField("Number of tweets to show", null=True, blank=True, choices=PACKERY_CHOICES, help_text=help_text('rca.HomePage', 'packery_tweets'))
    packery_research = models.IntegerField("Number of research items to show", null=True, blank=True, choices=PACKERY_CHOICES, help_text=help_text('rca.HomePage', 'packery_research'))
    packery_events = models.IntegerField("Number of events to show (excluding RCA Talks)", null=True, blank=True, choices=PACKERY_CHOICES, help_text=help_text('rca.HomePage', 'packery_events'))
    packery_events_rcatalks = models.IntegerField("Number of RCA Talk events to show", null=True, blank=True, choices=PACKERY_CHOICES, help_text=help_text('rca.HomePage', 'packery_events_rcatalks'))
    packery_blog = models.IntegerField("Number of blog items to show", null=True, blank=True, choices=PACKERY_CHOICES, help_text=help_text('rca.HomePage', 'packery_blog'))
    packery_student_stories = models.IntegerField("Number of student stories to show", null=True, blank=True, choices=PACKERY_CHOICES, help_text=help_text('rca.HomePage', 'packery_student_stories'))
    packery_alumni_stories = models.IntegerField("Number of alumni stories to show", null=True, blank=True, choices=PACKERY_CHOICES, help_text=help_text('rca.HomePage', 'packery_alumni_stories'))
    packery_student_work = models.IntegerField("Number of student work items to show", null=True, blank=True, choices=PACKERY_CHOICES, help_text=help_text('rca.HomePage', 'packery_student_work', default="Student pages flagged to Show On Homepage must have at least one carousel item"))
    packery_rcanow = models.IntegerField("Number of RCA Now items to show", null=True, blank=True, choices=PACKERY_CHOICES, help_text=help_text('rca.HomePage', 'packery_rcanow'))
    packery_review = models.IntegerField("Number of reviews to show", null=True, blank=True, choices=PACKERY_CHOICES, help_text=help_text('rca.HomePage', 'packery_review'))


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
        research = ResearchItem.objects.filter(live=True, show_on_homepage=True).order_by('random_order')
        events = EventItem.past_objects\
            .filter(live=True, show_on_homepage=True)\
            .exclude(audience='rcatalks')\
            .extra(select={
                'latest_date': "SELECT GREATEST(date_from, date_to) AS latest_date FROM rca_eventitemdatestimes where rca_eventitemdatestimes.page_id = wagtailcore_page.id ORDER BY latest_date DESC LIMIT 1",
            })\
            .order_by('-latest_date')
        events_rcatalks = EventItem.past_objects\
            .filter(live=True, show_on_homepage=True, audience='rcatalks')\
            .extra(select={
                'is_rca_talk': True,
                'latest_date': "SELECT GREATEST(date_from, date_to) AS latest_date FROM rca_eventitemdatestimes where rca_eventitemdatestimes.page_id = wagtailcore_page.id ORDER BY latest_date DESC LIMIT 1",
            })\
            .order_by('-latest_date')
        blog = RcaBlogPage.objects.filter(live=True, show_on_homepage=True).order_by('-date')
        student = NewStudentPage.objects.filter(live=True, show_on_homepage=True).order_by('random_order')
        rcanow = RcaNowPage.objects.filter(live=True, show_on_homepage=True).order_by('?')
        review = ReviewPage.objects.filter(live=True, show_on_homepage=True).order_by('?')
        tweets = [[], [], [], [], []]

        # Get all kinds of student stories
        student_stories_standard = StandardPage.objects\
            .filter(show_on_homepage=True, tags__name__iexact=StandardPage.STUDENT_STORY_TAG)\
            .exclude(tags__name__iexact=StandardPage.ALUMNI_STORY_TAG)\
            .values_list('pk', flat=True)
        student_stories_standard_stream = StandardStreamPage.objects\
            .filter(show_on_homepage=True, tags__name__iexact=StandardStreamPage.STUDENT_STORY_TAG)\
            .exclude(tags__name__iexact=StandardStreamPage.ALUMNI_STORY_TAG)\
            .values_list('pk', flat=True)

        student_stories = Page.objects.live()\
            .filter(models.Q(pk__in=student_stories_standard_stream) | models.Q(pk__in=student_stories_standard))\
            .annotate(is_student_story=models.Value(True, output_field=models.BooleanField())) \
            .order_by('?')

        # Get all kinds of alumni stories
        alumni_stories_standard = StandardPage.objects\
            .filter(show_on_homepage=True, tags__name__iexact=StandardPage.ALUMNI_STORY_TAG)\

        alumni_stories_standard_stream = StandardStreamPage.objects\
            .filter(show_on_homepage=True, tags__name__iexact=StandardStreamPage.ALUMNI_STORY_TAG)\

        alumni_stories = Page.objects.live()\
            .filter(models.Q(pk__in=alumni_stories_standard) | models.Q(pk__in=alumni_stories_standard_stream))\
            .annotate(is_alumni_story=models.Value(True, output_field=models.BooleanField()))\
            .order_by('?')

        if exclude:
            news = news.exclude(id__in=exclude)
            staff = staff.exclude(id__in=exclude)
            news = news.exclude(id__in=exclude)
            research = research.exclude(id__in=exclude)
            events = events.exclude(id__in=exclude)
            events_rcatalks = events_rcatalks.exclude(id__in=exclude)
            blog = blog.exclude(id__in=exclude)
            student_stories = student_stories.exclude(id__in=exclude)
            alumni_stories = alumni_stories.exclude(id__in=exclude)
            student = student.exclude(id__in=exclude)
            rcanow = rcanow.exclude(id__in=exclude)
            review = review.exclude(id__in=exclude)

        packery = list(chain(
            news[:self.packery_news],
            staff[:self.packery_staff],
            research[:self.packery_research],
            events[:self.packery_events],
            events_rcatalks[:self.packery_events_rcatalks],
            blog[:self.packery_blog],
            student_stories[:self.packery_student_stories],
            alumni_stories[:self.packery_alumni_stories],
            student[:self.packery_student_work],
            rcanow[:self.packery_rcanow],
            review[:self.packery_review],
        ))

        # only add tweets to the packery content if not using the plus button
        if not exclude:
            packery = packery + tweets[:self.packery_tweets]

        random.shuffle(packery)

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
        FieldPanel('packery_tweets'),
        FieldPanel('twitter_feed'),
        FieldPanel('packery_research'),
        FieldPanel('packery_events'),
        FieldPanel('packery_events_rcatalks'),
        FieldPanel('packery_blog'),
        FieldPanel('packery_student_stories'),
        FieldPanel('packery_alumni_stories'),
        FieldPanel('packery_student_work'),
        FieldPanel('packery_rcanow'),
        FieldPanel('packery_review'),
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
        SnippetChooserPanel('reusable_text_snippet'),
    ]

class JobPage(Page, SocialFields):
    school = models.ForeignKey('taxonomy.School', null=True, blank=True, on_delete=models.SET_NULL, related_name='job_pages', help_text=help_text('rca.JobPage', 'school'))
    programme = models.ForeignKey('taxonomy.Programme', null=True, blank=True, on_delete=models.SET_NULL, related_name='job_pages', help_text=help_text('rca.JobPage', 'programme'))
    area = models.ForeignKey('taxonomy.Area', null=True, blank=True, on_delete=models.SET_NULL, related_name='job_pages', help_text=help_text('rca.JobPage', 'area'))
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

    search_fields = Page.search_fields + [
        index.RelatedFields('school', [
            index.SearchField('display_name'),
        ]),
        index.RelatedFields('programme', [
            index.SearchField('display_name'),
        ]),
        index.RelatedFields('area', [
            index.SearchField('display_name'),
        ]),
        index.SearchField('other_department'),
        index.SearchField('get_campus_display'),
        index.SearchField('description'),
    ]

    search_name = 'Job'

JobPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('programme'),
    FieldPanel('school'),
    FieldPanel('area'),
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
        SnippetChooserPanel('ad'),
    ]

class JobsIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.JobsIndex', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.JobsIndex', 'body'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.JobsIndex', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.JobsIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

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


# == Staff profile page ==

class StaffPageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.StaffPage', related_name='carousel_items')

class StaffPageRole(Orderable):
    page = ParentalKey('rca.StaffPage', related_name='roles')
    title = models.CharField(max_length=255, help_text=help_text('rca.StaffPageRole', 'title'))
    school = models.ForeignKey('taxonomy.School', null=True, blank=True, on_delete=models.SET_NULL, related_name='staff_roles', help_text=help_text('rca.StaffPageRole', 'school'))
    programme = models.ForeignKey('taxonomy.Programme', null=True, blank=True, on_delete=models.SET_NULL, related_name='staff_roles', help_text=help_text('rca.StaffPageRole', 'programme'))
    area = models.ForeignKey('taxonomy.Area', null=True, blank=True, on_delete=models.SET_NULL, related_name='staff_roles', help_text=help_text('rca.StaffPageRole', 'area'))
    email = models.EmailField(max_length=255, blank=True, help_text=help_text('rca.StaffPageRole', 'email'))

    api_fields = [
        'title',
        'school',
        'programme',
        'area',
        'email',
    ]

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

    api_fields = [
        'title',
        'link',
        'text',
        'date',
    ]

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

    api_fields = [
        'title',
        'typeof',
        'location_year',
        'authors_collaborators',
        'link',
        'image',
    ]

    panels = [
        FieldPanel('title'),
        FieldPanel('typeof'),
        FieldPanel('location_year'),
        FieldPanel('authors_collaborators'),
        FieldPanel('link'),
        ImageChooserPanel('image'),
    ]

class StaffPage(Page, SocialFields):
    area = models.ForeignKey('taxonomy.Area', null=True, blank=True, on_delete=models.SET_NULL, related_name='staff', help_text=help_text('rca.StaffPage', 'area'))
    profile_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.StaffPage', 'profile_image'))
    staff_type = models.CharField(max_length=255, blank=True, choices=STAFF_TYPES_CHOICES, help_text=help_text('rca.StaffPage', 'staff_type'))
    staff_location = models.CharField(max_length=255, blank=True, choices=STAFF_LOCATION_CHOICES, help_text=help_text('rca.StaffPage', 'staff_location'))
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
    listing_intro = models.CharField(max_length=100, blank=True, help_text=help_text('rca.StaffPage', 'listing_intro'))
    research_interests = RichTextField(help_text=help_text('rca.StaffPage', 'research_interests'), blank=True)
    title_prefix = models.CharField(max_length=255, blank=True, help_text=help_text('rca.StaffPage', 'title_prefix'))
    first_name = models.CharField(max_length=255, help_text=help_text('rca.StaffPage', 'first_name'))
    last_name = models.CharField(max_length=255, help_text=help_text('rca.StaffPage', 'last_name'))
    supervised_student_other = models.CharField(max_length=255, blank=True, help_text=help_text('rca.StaffPage', 'supervised_student_other'))
    rca_content_id = models.CharField(max_length=255, blank=True, editable=False)  # for import
    random_order = models.IntegerField(null=True, blank=True, editable=False)
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.StaffPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))
    ad_username = models.CharField(max_length=255, blank=True, verbose_name='AD username', help_text=help_text('rca.StaffPage', 'ad_username'))

    search_fields = Page.search_fields + [
        index.RelatedFields('area', [
            index.SearchField('display_name'),
        ]),
        index.SearchField('get_staff_type_display'),
        index.SearchField('intro'),
        index.SearchField('biography'),
    ]

    api_fields = [
        'area',
        'profile_image',
        'staff_type',
        'staff_location',
        'twitter_feed',
        'intro',
        'biography',
        'practice',
        'publications_exhibtions_and_other_outcomes_placeholder',
        'external_collaborations_placeholder',
        'current_recent_research',
        'awards_and_grants',
        'listing_intro',
        'research_interests',
        'title_prefix',
        'first_name',
        'last_name',
        'supervised_student_other',
        'feed_image',
        'carousel_items',
        'roles',
        'collaborations',
        'publications_exhibitions',
        'ad_username',
    ]

    pushable_to_intranet = True

    search_name = 'Staff'


StaffPage.content_panels = [
    FieldPanel('title', classname="full title"),
    MultiFieldPanel([
        FieldPanel('title_prefix'),
        FieldPanel('first_name'),
        FieldPanel('last_name'),
    ], 'Full name'),
    FieldPanel('area'),
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
    FieldPanel('ad_username'),

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
        SnippetChooserPanel('ad'),
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
        school_slug = request.GET.get('school')
        programme_slug = request.GET.get('programme')
        area_slug = request.GET.get('area')

        # Programme
        programme_options = Programme.objects.filter(
            id__in=StaffPageRole.objects.values_list('programme', flat=True)
        )

        programme = programme_options.filter(slug=programme_slug).first()

        # School
        school_options = School.objects.filter(
            id__in=StaffPageRole.objects.values_list('school', flat=True)
        ) | School.objects.filter(
            id__in=StaffPageRole.objects.values_list('programme__school', flat=True)
        )

        school = school_options.filter(slug=school_slug).first()
        if school:
            # Filter programme options to only this school
            programme_options = programme_options.filter(school=school)

            # Prevent programme from a different school being selected
            if programme and programme.school != school:
                programme = None

        # Area
        area_options = Area.objects.filter(
            id__in=StaffPageRole.objects.values_list('area', flat=True)
        ) | Area.objects.filter(
            id__in=StaffPage.objects.values_list('area', flat=True)
        )

        area = area_options.filter(slug=area_slug).first()

        # Get staff pages
        staff_pages = StaffPage.objects.live()

        if programme:
            staff_pages = staff_pages.filter(roles__programme=programme)
        elif school:
            staff_pages = staff_pages.filter(
                models.Q(roles__school=school) |
                models.Q(roles__programme__school=school)
            )

        if area:
            staff_pages = staff_pages.filter(
                models.Q(area=area) |
                models.Q(roles__area=area)
            )

        if staff_type:
            staff_pages = staff_pages.filter(staff_type=staff_type)

        staff_pages = staff_pages.distinct().order_by('-random_order')

        # Paginate
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

        filters = [{
            "name": "school",
            "current_value": school.slug if school else None,
            "options": [""] + list(school_options.values_list('slug', flat=True)),
        }, {
            "name": "programme",
            "current_value": programme.slug if programme else None,
            "options": [""] + list(programme_options.values_list('slug', flat=True)),
        }, {
            "name": "staff_type",
            "current_value": staff_type,
            "options": [""] + list(dict(STAFF_TYPES_CHOICES).keys()),
        }, {
            "name": "area",
            "current_value": area.slug if area else None,
            "options": [""] + list(area_options.values_list('slug', flat=True)),
        }]

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
        SnippetChooserPanel('ad'),
    ]

class ResearchStudentIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.ResearchStudentIndex', 'intro'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ResearchStudentIndex', 'twitter_feed', default="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term"))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ResearchStudentIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

    search_name = None

    def all_students(self):
        students = NewStudentPageQuerySet(NewStudentPage).live()
        return students.mphil() | students.phd()

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        school_slug = request.GET.get('school')
        programme_slug = request.GET.get('programme')
        period = request.GET.get('period')

        # Get students
        students = NewStudentPageQuerySet(NewStudentPage).live()

        if period == 'current':
            mphil_students = students.mphil(current=True)
            phd_students = students.phd(current=True)
        elif period == 'past':
            mphil_students = students.mphil(current=False)
            phd_students = students.phd(current=False)
        else:
            mphil_students = students.mphil()
            phd_students = students.phd()

        students = mphil_students | phd_students

        # Get available programmes
        programme_options = Programme.objects.filter(
            models.Q(id__in=mphil_students.values_list('mphil_programme', flat=True)) |
            models.Q(id__in=phd_students.values_list('phd_programme', flat=True))
        )

        # Get all available schools
        # NOTE: this bit must be before we filter the programme listing by
        # school below
        school_options = School.objects.filter(programmes__in=programme_options).distinct()

        # If a school is selected, filter programme listing
        selected_school = school_options.filter(slug=school_slug).first()
        if selected_school:
            programme_options = programme_options.filter(school=selected_school)

        # Filter students by school/programme
        selected_programme = programme_options.filter(slug=programme_slug).first()
        if selected_programme:
            mphil_students = mphil_students.filter(mphil_programme=selected_programme)
            phd_students = phd_students.filter(phd_programme=selected_programme)
        elif selected_school:
            mphil_students = mphil_students.filter(mphil_programme__school=selected_school)
            phd_students = phd_students.filter(phd_programme__school=selected_school)

        students = (mphil_students | phd_students).distinct().order_by('random_order')

        # Pagination
        page = request.GET.get('page')
        paginator = Paginator(students, 17)  # Show 17 research students per page
        try:
            students = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            students = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            students = paginator.page(paginator.num_pages)

        filters = [
            {
                "name": "school",
                "current_value": selected_school.slug if selected_school else None,
                "options": [
                    school.slug for school in school_options
                ]
            },
            {
                "name": "programme",
                "current_value": selected_programme.slug if selected_programme else None,
                "options": [
                    programme.slug for programme in programme_options
                ]
            }
        ]

        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, "rca/includes/research_students_pages_listing.html", {
                'self': self,
                'research_students': students,
                'filters': json.dumps(filters),
            })
        else:
            return render(request, self.template, {
                'self': self,
                'research_students': students,
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


# == New Student page ==

class CarouselItemManager(models.Manager):
    use_for_related_fields = True

    def no_videos(self):
        return self.all().filter(embedly_url='')


class NewStudentPageQuerySet(PageQuerySet):
    def phd(self, school=None, programme=None, current=None, current_year=None, in_show=None):
        self = self.filter(phd_programme__isnull=False)

        if programme:
            self = self.filter(phd_programme=programme)

            if school and programme.school != school:
                return self.none()
        elif school:
            self = self.filter(phd_programme__school=school)

        if current is not None:
            if current_year is None:
                current_year = timezone.now().year

            empty_year_q = models.Q(phd_graduation_year='')
            if current == True:
                self = self.filter(models.Q(phd_graduation_year__gte=current_year) | empty_year_q)
            elif current == False:
                self = self.exclude(empty_year_q).filter(phd_graduation_year__lt=current_year)

        if in_show != None:
            self = self.filter(phd_in_show=in_show)

        return self

    def mphil(self, school=None, programme=None, current=None, current_year=None, in_show=None):
        self = self.filter(mphil_programme__isnull=False)

        if programme:
            self = self.filter(mphil_programme=programme)

            if school and programme.school != school:
                return self.none()
        elif school:
            self = self.filter(mphil_programme__school=school)

        if current is not None:
            if current_year is None:
                current_year = timezone.now().year

            empty_year_q = models.Q(mphil_graduation_year='')
            if current == True:
                self = self.filter(models.Q(mphil_graduation_year__gte=current_year) | empty_year_q)
            elif current == False:
                self = self.exclude(empty_year_q).filter(mphil_graduation_year__lt=current_year)

        if in_show != None:
            self = self.filter(mphil_in_show=in_show)

        return self

    def ma(self, school=None, programme=None, current=None, current_year=None, in_show=None):
        self = self.filter(ma_programme__isnull=False)

        if programme:
            self = self.filter(ma_programme=programme)

            if school and programme.school != school:
                return self.none()
        elif school:
            self = self.filter(ma_programme__school=school)

        if current is not None:
            if current_year is None:
                current_year = timezone.now().year

            if current == True:
                self = self.filter(ma_graduation_year=current_year)
            elif current == False:
                self = self.filter(ma_graduation_year__ne=current_year)

        if in_show != None:
            self = self.filter(ma_in_show=in_show)

        return self


# General
class NewStudentPagePreviousDegree(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='previous_degrees')
    degree = models.CharField(max_length=255, help_text=help_text('rca.NewStudentPagePreviousDegree', 'degree', default="Please include the degree level, subject, institution name and year of graduation, separated by commas"))

    api_fields = ['degree']
    panels = [FieldPanel('degree')]

class NewStudentPageExhibition(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='exhibitions')
    exhibition = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageExhibition', 'exhibition', default="Please include exhibition title, gallery, city and year, separated by commas"))

    api_fields = ['exhibition']
    panels = [FieldPanel('exhibition')]

class NewStudentPageExperience(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='experiences')
    experience = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageExperience', 'experience', default="Please include job title, company name, city and year(s), separated by commas"))

    api_fields = ['experience']
    panels = [FieldPanel('experience')]

class NewStudentPageContactsEmail(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='emails')
    email = models.EmailField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageContactsEmail', 'email', default="Students can use personal email as well as firstname.surname@network.rca.ac.uk"))

    api_fields = ['email']
    panels = [FieldPanel('email')]

class NewStudentPageContactsPhone(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='phones')
    phone = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageContactsPhone', 'phone', default="UK mobile e.g. 07XXX XXXXXX or overseas landline, e.g. +33 (1) XXXXXXX"))

    api_fields = ['phone']
    panels = [FieldPanel('phone')]

class NewStudentPageContactsWebsite(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='websites')
    website = models.URLField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageContactsWebsite', 'website'))

    api_fields = ['website']
    panels = [FieldPanel('website')]

class NewStudentPagePublication(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='publications')
    name = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPagePublication', 'name', default="Please include author (if not you), title of article, title of publication, issue number, year, pages, separated by commas"))

    api_fields = ['name']
    panels = [FieldPanel('name')]

class NewStudentPageConference(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='conferences')
    name = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageConference', 'name', default="Please include paper, title of conference, institution, date, separated by commas"))

    api_fields = ['name']
    panels = [FieldPanel('name')]

class NewStudentPageAward(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='awards')
    award = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageAward', 'award', default="Please include prize, award title and year, separated by commas"))

    api_fields = ['award']
    panels = [FieldPanel('award')]


# Show
class NewStudentPageShowCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.NewStudentPage', related_name='show_carousel_items')

    objects = CarouselItemManager()

class NewStudentPageShowCollaborator(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='show_collaborators')
    name = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageShowCollaborator', 'name', default="Please include collaborator's name and programme (if RCA), separated by commas"))

    api_fields = ['name']
    panels = [FieldPanel('name')]

class NewStudentPageShowSponsor(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='show_sponsors')
    name = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageShowSponsor', 'name', default="Please list companies and individuals that have provided financial or in kind sponsorship for your final project, separated by commas"))

    api_fields = ['name']
    panels = [FieldPanel('name')]


# MPhil
class NewStudentPageMPhilCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.NewStudentPage', related_name='mphil_carousel_items')

    objects = CarouselItemManager()

class NewStudentPageMPhilCollaborator(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='mphil_collaborators')
    name = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageMPhilCollaborator', 'name', default="Please include collaborator's name and programme (if RCA), separated by commas"))

    api_fields = ['name']
    panels = [FieldPanel('name')]

class NewStudentPageMPhilSponsor(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='mphil_sponsors')
    name = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPageMPhilSponsor', 'name', default="Please list companies and individuals that have provided financial or in kind sponsorship for your final project, separated by commas"))

    api_fields = ['name']
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

    api_fields = ['name', 'link']

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

    api_fields = ['name']
    panels = [FieldPanel('name')]

class NewStudentPagePhDSponsor(Orderable):
    page = ParentalKey('rca.NewStudentPage', related_name='phd_sponsors')
    name = models.CharField(max_length=255, blank=True, help_text=help_text('rca.NewStudentPagePhDSponsor', 'name', default="Please list companies and individuals that have provided financial or in kind sponsorship for your final project, separated by commas"))

    api_fields = ['name']
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

    api_fields = ['name', 'link']

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
    ad_username = models.CharField(max_length=255, blank=True, verbose_name='AD username', help_text=help_text('rca.StudentPage', 'ad_username'))

    # Hidden fields
    rca_content_id = models.CharField(max_length=255, blank=True, editable=False)  # for import
    random_order = models.IntegerField(null=True, blank=True, editable=False)

    # MA details
    ma_programme = models.ForeignKey('taxonomy.Programme', verbose_name="Programme", null=True, blank=True, on_delete=models.SET_NULL, related_name='ma_students', help_text=help_text('rca.NewStudentPage', 'ma_programme'))
    ma_graduation_year = models.CharField("Graduation year",max_length=4, blank=True, help_text=help_text('rca.NewStudentPage', 'ma_graduation_year'))
    ma_specialism = models.CharField("Specialism", max_length=255, choices=SPECIALISM_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'ma_specialism'))
    ma_in_show = models.BooleanField("In show", default=False, help_text=help_text('rca.NewStudentPage', 'ma_in_show', default="Please tick only if you're in the Show this academic year"))
    show_work_title = models.CharField("Dissertation/project title", max_length=255, blank=True, help_text=help_text('rca.NewStudentPage', 'show_work_title'))
    show_work_type = models.CharField("Work type", max_length=255, choices=SHOW_WORK_TYPE_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'show_work_type'))
    show_work_location = models.CharField("Work location", max_length=255, choices=CAMPUS_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'show_work_location'))
    show_work_description = RichTextField(help_text=help_text('rca.NewStudentPage', 'show_work_description'), blank=True)

    # MPhil details
    mphil_programme = models.ForeignKey('taxonomy.Programme', verbose_name="Programme", null=True, blank=True, on_delete=models.SET_NULL, related_name='mphil_students', help_text=help_text('rca.NewStudentPage', 'mphil_programme'))
    mphil_school = models.ForeignKey('taxonomy.School', verbose_name="School", null=True, blank=True, on_delete=models.SET_NULL, related_name='mphil_students', help_text=help_text('rca.NewStudentPage', 'mphil_school'))
    mphil_start_year = models.CharField("Start year", max_length=4, blank=True, help_text=help_text('rca.NewStudentPage', 'mphil_start_year'))
    mphil_graduation_year = models.CharField("Graduation year", max_length=4, blank=True, help_text=help_text('rca.NewStudentPage', 'mphil_graduation_year'))
    mphil_work_location = models.CharField("Work location", max_length=255, choices=CAMPUS_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'mphil_work_location'))
    mphil_dissertation_title = models.CharField("Dissertation title", max_length=255, blank=True, help_text=help_text('rca.NewStudentPage', 'mphil_dissertation_title'))
    mphil_statement = RichTextField(help_text=help_text('rca.NewStudentPage', 'mphil_statement'), blank=True)
    mphil_in_show = models.BooleanField("In show", default=False, help_text=help_text('rca.NewStudentPage', 'mphil_in_show', default="Please tick only if you're in the Show this academic year"))
    mphil_status = models.CharField("Status", max_length=255, choices=STATUS_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'mphil_status', default=''))
    mphil_degree_type = models.CharField("Degree type", max_length=255, choices=DEGREE_TYPE_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'mphil_degree_type'))

    # PhD details
    phd_programme = models.ForeignKey('taxonomy.Programme', verbose_name="Programme", null=True, blank=True, on_delete=models.SET_NULL, related_name='phd_students', help_text=help_text('rca.NewStudentPage', 'phd_programme'))
    phd_school = models.ForeignKey('taxonomy.School', verbose_name="School", null=True, blank=True, on_delete=models.SET_NULL, related_name='phd_students', help_text=help_text('rca.NewStudentPage', 'phd_school'))
    phd_start_year = models.CharField("Start year", max_length=4, blank=True, help_text=help_text('rca.NewStudentPage', 'phd_start_year'))
    phd_graduation_year = models.CharField("Graduation year", max_length=4, blank=True, help_text=help_text('rca.NewStudentPage', 'phd_graduation_year'))
    phd_work_location = models.CharField("Work location", max_length=255, choices=CAMPUS_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'phd_work_location'))
    phd_dissertation_title = models.CharField("Dissertation title", max_length=255, blank=True, help_text=help_text('rca.NewStudentPage', 'phd_dissertation_title'))
    phd_statement = RichTextField(help_text=help_text('rca.NewStudentPage', 'phd_statement'), blank=True)
    phd_in_show = models.BooleanField("In show", default=False, help_text=help_text('rca.NewStudentPage', 'phd_in_show', default="Please tick only if you're in the Show this academic year"))
    phd_status = models.CharField("Status", max_length=255, choices=STATUS_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'phd_status', default=''))
    phd_degree_type = models.CharField("Degree type", max_length=255, choices=DEGREE_TYPE_CHOICES, blank=True, help_text=help_text('rca.NewStudentPage', 'phd_degree_type'))

    search_fields = Page.search_fields + [
        index.SearchField('first_name', partial_match=True, boost=2),
        index.SearchField('last_name', partial_match=True, boost=2),
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
        index.FilterField('ma_programme'),
        index.FilterField('ma_graduation_year'),

        index.SearchField('get_mphil_school_display'),
        index.SearchField('get_mphil_programme_display'),
        index.SearchField('mphil_graduation_year'),
        index.SearchField('mphil_dissertation_title'),
        index.SearchField('mphil_statement'),
        index.FilterField('mphil_in_show'),
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
        index.FilterField('phd_programme'),
        index.FilterField('phd_graduation_year'),
        index.FilterField('phd_status'),
        index.FilterField('phd_degree_type'),
    ]

    api_fields = [
        'first_name',
        'last_name',
        'profile_image',
        'statement',
        'twitter_handle',
        'funding',
        'feed_image',
        'innovation_rca_fellow',
        'ad_username',
        'postcard_image',
        'previous_degrees',
        'exhibitions',
        'experiences',
        'emails',
        'phones',
        'websites',
        'publications',
        'conferences',
        'awards',

        # MA details
        'ma_programme',
        'ma_graduation_year',
        'ma_specialism',
        'ma_in_show',
        'show_work_title',
        'show_work_type',
        'show_work_location',
        'show_work_description',
        'show_carousel_items',
        'show_collaborators',
        'show_sponsors',

        # MPhil details
        'mphil_programme',
        'mphil_school',
        'mphil_start_year',
        'mphil_graduation_year',
        'mphil_work_location',
        'mphil_dissertation_title',
        'mphil_statement',
        'mphil_in_show',
        'mphil_status',
        'mphil_degree_type',
        'mphil_carousel_items',
        'mphil_collaborators',
        'mphil_sponsors',
        'mphil_supervisors',

        # PhD details
        'phd_programme',
        'phd_school',
        'phd_start_year',
        'phd_graduation_year',
        'phd_work_location',
        'phd_dissertation_title',
        'phd_statement',
        'phd_in_show',
        'phd_status',
        'phd_degree_type',
        'phd_carousel_items',
        'phd_collaborators',
        'phd_sponsors',
        'phd_supervisors',
    ]

    pushable_to_intranet = True

    def clean(self):
        SCHOOL_PROGRAMME_ERROR = 'Please only select a School if your degree ' \
                                 'is not associated with a specific programme.'
        # Make sure both options - MPhil and PhD - are not selected
        errors = {}
        
        if self.phd_programme and self.phd_school:
            errors['phd_school'] = [SCHOOL_PROGRAMME_ERROR]

        if self.mphil_programme and self.mphil_school:
            errors['mphil_school'] = [SCHOOL_PROGRAMME_ERROR]

        if any(errors.values()):
            raise ValidationError(errors)
        
        # If MPhil details are filled in, please require programme or school
        # field
        PHD_MPHIL_EMPTY_MSG = 'Please choose programme or school option.'
        
        mphil_fields = [f for f in self._meta.get_fields() if f.concrete \
                            and f.name.startswith('mphil') \
                            and getattr(self, f.name) \
                            and f.name not in ('mphil_programme', 'mphil_school')]

        if mphil_fields and not self.mphil_programme and not self.mphil_school:
    
            errors = {
                'mphil_school': PHD_MPHIL_EMPTY_MSG,
                'mphil_programme': PHD_MPHIL_EMPTY_MSG
            }

            errors.update({f.name: PHD_MPHIL_EMPTY_MSG for f in mphil_fields})

            raise ValidationError(errors)

        # If PhD details are filled in, please require programme or school
        # field
        phd_fields = [f for f in self._meta.get_fields() if f.concrete \
                            and f.name.startswith('phd') \
                            and getattr(self, f.name) \
                            and f.name not in ('phd_programme', 'phd_school')]

        if phd_fields and not self.phd_programme and not self.phd_school:

            errors = {
                'phd_school': PHD_MPHIL_EMPTY_MSG,
                'phd_programme': PHD_MPHIL_EMPTY_MSG
            }

            errors.update({f.name: PHD_MPHIL_EMPTY_MSG for f in phd_fields})

            raise ValidationError(errors)

    @property
    def is_ma_student(self):
        return self.ma_programme is not None

    @property
    def is_mphil_student(self):
        return self.get_mphil_school() is not None

    @property
    def is_phd_student(self):
        return self.get_phd_school() is not None

    def get_profiles(self):
        profiles = {}

        if self.is_phd_student:
            profiles['phd'] = {
                'name': "PhD",
                'school': self.get_phd_school(),
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
                'school': self.get_mphil_school(),
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
                'school': self.ma_programme.school,
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

    def get_ma_programme_display(self):
        if not self.ma_programme:
            return ''

        return self.ma_programme.get_display_name_for_year(self.ma_graduation_year)

    def get_ma_school_display(self):
        if not self.ma_programme:
            return ''

        return self.ma_programme.school.get_display_name_for_year(self.ma_graduation_year)

    def get_mphil_programme_display(self):
        if not self.mphil_programme:
            return ''

        return self.mphil_programme.get_display_name_for_year(self.mphil_graduation_year)

    def get_mphil_school(self):
        if self.mphil_programme:
            return self.mphil_programme.school

        return self.mphil_school

    def get_mphil_school_display(self):
        mphil_school = self.get_mphil_school()

        if mphil_school:
            return mphil_school.get_display_name_for_year(self.mphil_graduation_year)

    def get_phd_programme_display(self):
        if not self.phd_programme:
            return ''

        return self.phd_programme.get_display_name_for_year(self.phd_graduation_year)

    def get_phd_school(self):
        if self.phd_programme:
            return self.phd_programme.school

        return self.phd_school

    def get_phd_school_display(self):
        phd_school = self.get_phd_school()

        if not phd_school:
            return ''

        return phd_school.get_display_name_for_year(self.phd_graduation_year)

    def get_programme_display(self):
        profile = self.get_profile()

        if profile:
            return self.get_profile()['programme_display']
        else:
            return ''

    def get_school_display(self):
        profile = self.get_profile()

        if profile:
            return self.get_profile()['school_display']
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
            for gallery_page in GalleryPage.objects.live():
                if gallery_page.all_students().filter(id=self.id).exists():
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
    FieldPanel('ad_username'),
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
        FieldPanel('mphil_programme'),
        FieldPanel('mphil_school'),
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
        FieldPanel('phd_programme'),
        FieldPanel('phd_school'),
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
    area = models.ForeignKey('taxonomy.Area', null=True, on_delete=models.SET_NULL, related_name='rca_now_pages', help_text=help_text('rca.RcaNowPageArea', 'area'))

    panels = [FieldPanel('area')]


class RcaNowPageRelatedLink(Orderable):
    page = ParentalKey('rca.RcaNowPage', related_name='related_links')
    link = models.URLField(max_length=255, blank=True, help_text=help_text('rca.RcaNowPageRelatedLink', 'link'))

    panels = [FieldPanel('link')]


class RcaNowPage(Page, SocialFields):
    body = RichTextField(help_text=help_text('rca.RcaNowPage', 'body'))
    author = models.CharField(max_length=255, blank=True, help_text=help_text('rca.RcaNowPage', 'author'))
    date = models.DateField("Creation date", help_text=help_text('rca.RcaNowPage', 'date'))
    programme = models.ForeignKey('taxonomy.Programme', null=True, blank=True, on_delete=models.SET_NULL, related_name='rca_now_pages', help_text=help_text('rca.RcaNowPage', 'programme'))
    school = models.ForeignKey('taxonomy.School', null=True, blank=True, on_delete=models.SET_NULL, related_name='rca_now_pages', help_text=help_text('rca.RcaNowPage', 'school'))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.RcaNowPage', 'show_on_homepage'))
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.RcaNowPage', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.RcaNowPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    tags = ClusterTaggableManager(through=RcaNowPageTag)

    search_fields = Page.search_fields + [
        index.SearchField('body'),
        index.SearchField('author'),
        index.RelatedFields('school', [
            index.SearchField('display_name'),
        ]),
        index.RelatedFields('programme', [
            index.SearchField('display_name'),
        ]),
    ]

    search_name = 'RCA Now'

    class Meta:
        verbose_name = 'RCA Now Page'

    def author_profile_page(self):
        """Return the profile page for the author of this post, if one exists (and is live)"""
        if self.owner:
            try:
                return NewStudentPage.objects.filter(live=True, owner=self.owner)[0]
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

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    search_name = None

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        programme_slug = request.GET.get('programme')
        school_slug = request.GET.get('school')
        area_slug = request.GET.get('area')

        # Programme
        programme_options = Programme.objects.filter(
            id__in=RcaNowPage.objects.live().values_list('programme', flat=True)
        )
        programme = programme_options.filter(slug=programme_slug).first()

        # School
        school_options = School.objects.filter(
            id__in=RcaNowPage.objects.live().values_list('school', flat=True)
        ) | School.objects.filter(
            id__in=RcaNowPage.objects.live().values_list('programme__school', flat=True)
        )
        school = school_options.filter(slug=school_slug).first()

        if school:
            # Filter programme options to only this school
            programme_options = programme_options.filter(school=school)
            # Prevent programme from a different school being selected
            if programme and programme.school != school:
                programme = None

        # Area
        area_options = Area.objects.filter(
            id__in=RcaNowPageArea.objects.filter(page__live=True).values_list('area', flat=True)
        )
        area = area_options.filter(slug=area_slug).first()

        # Get RCA Now items
        rca_now_items = RcaNowPage.objects.live()

        if programme:
            rca_now_items = rca_now_items.filter(programme=programme)
        elif school:
            rca_now_items = rca_now_items.filter(
                models.Q(school=school) |
                models.Q(programme__school=school)
            )

        if area:
            rca_now_items = rca_now_items.filter(models.Q(areas__area=area))

        rca_now_items = rca_now_items.order_by('-date')

        # Pagination
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

        filters = [{
            "name": "school",
            "current_value": school.slug if school else None,
            "options": [""] + list(school_options.values_list('slug', flat=True)),
        }, {
            "name": "programme",
            "current_value": programme.slug if programme else None,
            "options": [""] + list(programme_options.values_list('slug', flat=True)),
        }, {
            "name": "area",
            "current_value": area.slug if area else None,
            "options": [""] + list(area_options.values_list('slug', flat=True)),
        }]

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
    area = models.ForeignKey('taxonomy.Area', null=True, on_delete=models.SET_NULL, related_name='blog_pages', help_text=help_text('rca.RcaBlogPageArea', 'area'))

    api_fields = [
        'area',
    ]

    panels = [FieldPanel('area')]


class RcaBlogPage(Page, SocialFields):
    body = RichTextField(help_text=help_text('rca.RcaBlogPage', 'body'))
    author = models.CharField(max_length=255, blank=True, help_text=help_text('rca.RcaBlogPage', 'author'))
    date = models.DateField("Creation date", help_text=help_text('rca.RcaBlogPage', 'date'))
    programme = models.ForeignKey('taxonomy.Programme', null=True, blank=True, on_delete=models.SET_NULL, related_name='rca_blog_pages', help_text=help_text('rca.RcaBlogPage', 'programme'))
    school = models.ForeignKey('taxonomy.School', null=True, blank=True, on_delete=models.SET_NULL, related_name='rca_blog_pages', help_text=help_text('rca.RcaBlogPage', 'school'))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.RcaBlogPage', 'show_on_homepage'))
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.RcaBlogPage', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, on_delete=models.SET_NULL, blank=True, related_name='+', help_text=help_text('rca.RcaBlogPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    tags = ClusterTaggableManager(through=RcaBlogPageTag)

    search_fields = Page.search_fields + [
        index.SearchField('body'),
        index.SearchField('author'),
        index.RelatedFields('school', [
            index.SearchField('display_name'),
        ]),
        index.RelatedFields('programme', [
            index.SearchField('display_name'),
        ]),
        index.RelatedFields('areas', [
            index.RelatedFields('area', [
                index.SearchField('display_name'),
            ]),
        ]),
    ]

    api_fields = [
        'body',
        'author',
        'date',
        'programme',
        'school',
        'twitter_feed',
        'feed_image',
        'tags',
        'carousel_items',
        'areas',
    ]

    pushable_to_intranet = True

    search_name = 'RCA Blog'

    class Meta:
        verbose_name = 'Blog Page'

    def author_profile_page(self):
        """Return the profile page for the author of this post, if one exists (and is live)"""
        if self.owner:
            try:
                return NewStudentPage.objects.filter(live=True, owner=self.owner)[0]
            except IndexError:
                return None

    def blog_index(self):
        """Return the parent blog index for the blog page, so that it can be displayed in the Homepage packery area"""
        return self.get_ancestors().type(RcaBlogIndex).last()

    def get_related_blogs(self, count=4):
        return RcaBlogPage.objects.live().sibling_of(self, inclusive=False).order_by('-date')[:count]


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

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

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
        tag = request.GET.get('tag', None)
        rca_blog_items = self.get_blog_items(tag=tag).order_by('-date')

        # Pagination
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
            })
        else:
            return render(request, self.template, {
                'self': self,
                'rca_blog_items': rca_blog_items,
                'tag': tag,
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
    school = models.ForeignKey('taxonomy.School', null=True, blank=True, on_delete=models.SET_NULL, related_name='research_items', help_text=help_text('rca.ResearchItem', 'school'))
    programme = models.ForeignKey('taxonomy.Programme', null=True, blank=True, on_delete=models.SET_NULL, related_name='research_items', help_text=help_text('rca.ResearchItem', 'programme'))
    work_type = models.CharField(max_length=255, choices=WORK_TYPES_CHOICES, help_text=help_text('rca.ResearchItem', 'work_type'))
    work_type_other = models.CharField("'Other' work type", max_length=255, blank=True, help_text=help_text('rca.ResearchItem', 'work_type_other'))
    theme = models.CharField(max_length=255, choices=WORK_THEME_CHOICES, blank=True, help_text=help_text('rca.ResearchItem', 'theme'))
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ResearchItem', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    rca_content_id = models.CharField(max_length=255, blank=True, editable=False) # for import
    eprintid = models.CharField(max_length=255, blank=True, editable=False) # for import
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.ResearchItem', 'show_on_homepage'))
    random_order = models.IntegerField(null=True, blank=True, editable=False)
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ResearchItem', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))
    featured = models.BooleanField(default=False, blank=True, help_text=help_text('rca.ResearchItem', 'featured'))

    search_fields = Page.search_fields + [
        index.SearchField('subtitle'),
        index.SearchField('get_research_type_display'),
        index.SearchField('description'),
        index.RelatedFields('school', [
            index.SearchField('display_name'),
        ]),
        index.RelatedFields('programme', [
            index.SearchField('display_name'),
        ]),
        index.SearchField('get_work_type_display'),
        index.SearchField('work_type_other'),
        index.SearchField('get_theme_display'),
    ]

    search_name = 'Research'

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        # Get related research
        research_items = ResearchItem.objects.filter(live=True).order_by('random_order')
        if self.programme:
            research_items = research_items.filter(programme=self.programme)
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
            areas=Area.objects.filter(slug='research'),
            programmes=Programme.objects.filter(id=self.programme_id) if self.programme_id else None,
            schools=School.objects.filter(id=self.school_id) if self.school_id else None,
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
        FieldPanel('featured'),
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
        SnippetChooserPanel('ad'),
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
    news_carousel_area = models.ForeignKey('taxonomy.Area', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ResearchInnovationPage', 'news_carousel_area'))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ResearchInnovationPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

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
        SnippetChooserPanel('ad'),
    ]

class CurrentResearchPage(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.CurrentResearchPage', 'intro'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.CurrentResearchPage', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.CurrentResearchPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    indexed = False

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        research_type = request.GET.get('research_type')
        school_slug = request.GET.get('school')
        theme = request.GET.get('theme')
        work_type = request.GET.get('work_type')

        research_items = ResearchItem.objects.live().filter(featured=True)

        # Research type
        research_type_options = list(zip(*RESEARCH_TYPES_CHOICES)[0])
        if research_type in research_type_options:
            research_items = research_items.filter(research_type=research_type)
        else:
            research_type = ''

        # School
        school_options = School.objects.filter(
            id__in=research_items.values_list('school', flat=True)
        ) | School.objects.filter(
            id__in=research_items.values_list('programme__school', flat=True)
        )
        school = school_options.filter(slug=school_slug).first()

        if school:
            research_items = research_items.filter(
                models.Q(school=school) |
                models.Q(programme__school=school)
            )

        # Theme
        available_themes = set(research_items.values_list('theme', flat=True))
        theme_options = [t for t in zip(*WORK_THEME_CHOICES)[0] if t in available_themes]
        if theme in theme_options:
            research_items = research_items.filter(theme=theme)
        else:
            theme = ''

        # Work type
        available_work_types = set(research_items.values_list('work_type', flat=True))
        work_type_options = [wt for wt in zip(*WORK_TYPES_CHOICES)[0] if wt in available_work_types]
        if work_type in work_type_options:
            research_items = research_items.filter(work_type=work_type)
        else:
            work_type = ''

        research_items = research_items.order_by('random_order')

        # Pagination
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

        filters = [{
            "name": "research_type",
            "current_value": research_type,
            "options": [""] + research_type_options,

        }, {
            "name": "school",
            "current_value": school.slug if school else None,
            "options": [""] + list(school_options.values_list('slug', flat=True)),
        }, {
            "name": "theme",
            "current_value": theme,
            "options": [""] + theme_options,
        }, {
            "name": "work_type",
            "current_value": work_type,
            "options": [""] + work_type_options,
        }]

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

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    search_name = 'Gallery'

    def student_which_profile(self, student, ma_students, mphil_students, phd_students):
        # Check if student is in phd students
        if phd_students.filter(pk=student.pk).exists():
            return 'phd'

        # Check if student is in mphil students
        if mphil_students.filter(pk=student.pk).exists():
            return 'mphil'

        # Check if student is in ma students
        if ma_students.filter(pk=student.pk).exists():
            return 'ma'

    def all_students(self):
        students = NewStudentPageQuerySet(NewStudentPage).live()
        return students.ma(in_show=True) | students.mphil(in_show=True) | students.phd(in_show=True)

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        # Get filter parameters
        school_slug = request.GET.get('school')
        programme_slug = request.GET.get('programme')
        year = request.GET.get('degree_year') or None  # "or None" converts '' => None

        # Get students
        students = NewStudentPageQuerySet(NewStudentPage).live()

        if year:
            ma_students = students.ma(in_show=True, current=True, current_year=year)
            mphil_students = students.none()
            phd_students = students.none()
        else:
            # Students for all time
            ma_students = students.ma(in_show=True)
            mphil_students = students.mphil(in_show=True)
            phd_students = students.phd(in_show=True)

        # Get available years
        # NOTE: We need to use the un-year-filtered students list here, unlike
        # for the programme_options
        year_options = list()
        year_options.extend(students.ma(in_show=True).exclude(ma_graduation_year='').values_list('ma_graduation_year', flat=True))
        year_options.extend(students.mphil(in_show=True).exclude(mphil_graduation_year='').values_list('mphil_graduation_year', flat=True))
        year_options.extend(students.phd(in_show=True).exclude(phd_graduation_year='').values_list('phd_graduation_year', flat=True))
        year_options = list(set(year_options))
        year_options.sort(reverse=True)

        # Get available programmes
        programme_options = Programme.objects.filter(
            models.Q(id__in=ma_students.values_list('ma_programme', flat=True)) |
            models.Q(id__in=mphil_students.values_list('mphil_programme', flat=True)) |
            models.Q(id__in=phd_students.values_list('phd_programme', flat=True))
        ).order_by('slug').distinct('slug')

        # Get all available schools
        # NOTE: this bit must be before we filter the programme listing by
        # school below
        school_options = School.objects.filter(programmes__in=programme_options).distinct()

        # If a school is selected, filter programme listing
        selected_school = school_options.filter(slug=school_slug).first()
        if selected_school:
            programme_options = programme_options.filter(school=selected_school)

        # Filter students by school/programme
        selected_programme = programme_options.filter(slug=programme_slug).first()
        if selected_programme:
            ma_students = ma_students.filter(ma_programme=selected_programme)
            mphil_students = mphil_students.filter(mphil_programme=selected_programme)
            phd_students = phd_students.filter(phd_programme=selected_programme)
        elif selected_school:
            ma_students = ma_students.filter(ma_programme__school=selected_school)
            mphil_students = mphil_students.filter(mphil_programme__school=selected_school)
            phd_students = phd_students.filter(phd_programme__school=selected_school)

        students = (ma_students | mphil_students | phd_students).distinct().order_by('random_order')

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
        # NOTE: Runs queries for each student, so must be done after pagination!
        for student in students:
            student.profile = student.get_profile(self.student_which_profile(student, ma_students, mphil_students, phd_students))

        # Get template
        if request.is_ajax() and 'pjax' not in request.GET:
            template = 'rca/includes/gallery_listing.html'
        else:
            template = self.template

        filters = [
            {
                "name": "school",
                "current_value": selected_school.slug if selected_school else None,
                "options": [
                    school.slug for school in school_options
                ]
            }, {
                "name": "programme",
                "current_value": selected_programme.slug if selected_programme else None,
                "options": [
                    programme.slug for programme in programme_options
                ]
            }, {
                "name": "year",
                "current_value": year,
                "options": list(year_options)
            }
        ]

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
                student_page = self.all_students().get(slug=path_components[0])
                return RouteResult(student_page.specific, kwargs={'view': 'show'})
            except NewStudentPage.DoesNotExist:
                pass

        return super(GalleryPage, self).route(request, path_components)


GalleryPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    FieldPanel('twitter_feed'),
    InlinePanel("related_links", label="Related links")
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


class ContactUsPageContactFields(models.Model):
    contact_snippet = models.ForeignKey('rca.ContactSnippet', null=True, blank=True, related_name='+', help_text=help_text('rca.ContactUsPageGeneralEnquiries', 'contact_snippet'))
    text = RichTextField(blank=True, help_text=help_text('rca.ContactUsPageGeneralEnquiries', 'text'))

    def clean(self):
        if not self.contact_snippet and not self.text:
            raise ValidationError({
                'contact_snippet': ValidationError("You must fill in the contact snippet field or the text field."),
                'text': ValidationError("You must fill in the contact snippet field or the text field."),
            })

        if self.contact_snippet and self.text:
            raise ValidationError({
                'contact_snippet': ValidationError("You must fill in the contact snippet field or the text field. You can't use both."),
                'text': ValidationError("You must fill in the contact snippet field or the text field. You can't use both."),
            })

    class Meta:
        abstract = True


ContactUsPageContactFields.panels = [
    MultiFieldPanel([
        SnippetChooserPanel('contact_snippet'),
        FieldPanel('text'),
    ], heading="Contact fields")
]


class ContactUsPageProgrammeContact(Orderable, ContactUsPageContactFields):
    page = ParentalKey('rca.ContactUsPage', related_name='programme_contacts')
    programme = models.ForeignKey('taxonomy.Programme', null=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ContactUsPage', 'programme'))


ContactUsPageProgrammeContact.panels = [
    FieldPanel('programme'),
] + ContactUsPageContactFields.panels


class ContactUsPageGeneralEnquiries(Orderable, ContactUsPageContactFields):
    page = ParentalKey('rca.ContactUsPage', related_name='general_enquiries')


ContactUsPageGeneralEnquiries.panels = ContactUsPageContactFields.panels


class ContactUsPageMiddleColumnLinks(Orderable):
    page = ParentalKey('rca.ContactUsPage', related_name='middle_column_links')
    link_page = models.ForeignKey('wagtailcore.Page', on_delete=models.CASCADE, related_name='+', blank=True, null=True)


ContactUsPageMiddleColumnLinks.panels = [
    PageChooserPanel('link_page'),
]


class ContactUsPage(Page, SocialFields, SidebarBehaviourFields):
    body = RichTextField(blank=True, help_text=help_text('rca.ContactUsPage', 'body'))
    middle_column_map = models.TextField(blank=True, help_text=help_text('rca.ContactUsPage', 'middle_column_map'))
    contact_form_page = models.ForeignKey('rca.EnquiryFormPage', null=True, blank=True, related_name='contact_form_page', on_delete=models.SET_NULL)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ContactUsPage', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))

    search_fields = Page.search_fields + [
        index.SearchField('body'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super(ContactUsPage, self).get_context(request, *args, **kwargs)

        if request.is_ajax() and request.GET.get('format') == 'programme_contact_form':
            programme_contact = self.programme_contacts.filter(
                programme__disabled=False,
                pk=request.GET.get('programme_contact')
            )
            programme_contact = programme_contact.first()

            context.update({
                'form': self.contact_form_page.get_form() if self.contact_form_page else None,
                'programme_contact': programme_contact,
            })

        return context

    def get_template(self, request, *args, **kwargs):
        if request.is_ajax() and request.GET.get('format') == 'programme_contact_form':
            return 'rca/contact_us_page_programme_contact_form_ajax.html'

        return super(ContactUsPage, self).get_template(request, *args, **kwargs)

    @vary_on_headers('X-Requested-With')
    def serve(self, request, *args, **kwargs):
        return super(ContactUsPage, self).serve(request, *args, **kwargs)

ContactUsPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('body', classname="full"),
    PageChooserPanel('contact_form_page', page_type='rca.EnquiryFormPage'),
    InlinePanel('general_enquiries', label='General enquiries'),
    InlinePanel('programme_contacts', label='Programme contacts'),
    FieldPanel('middle_column_map', classname="full"),
    InlinePanel('middle_column_links', label='Middle column links'),
    FieldPanel('twitter_feed'),
]

ContactUsPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]

ContactUsPage.settings_panels = [
    PublishingPanel(),
    MultiFieldPanel([
        FieldPanel('collapse_upcoming_events'),
    ], 'Sidebar behaviour'),
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

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

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

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

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
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.InnovationRCAProject', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.InnovationRCAProject', 'show_on_homepage'))
    project_type = models.CharField(max_length=255, choices=INNOVATIONRCA_PROJECT_TYPES_CHOICES, help_text=help_text('rca.InnovationRCAProject', 'project_type'))
    project_ended = models.BooleanField(default=False, help_text=help_text('rca.InnovationRCAProject', 'project_ended'))
    random_order = models.IntegerField(null=True, blank=True, editable=False)
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.InnovationRCAProject', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + [
        index.SearchField('subtitle'),
        index.SearchField('description'),
        index.SearchField('get_project_type_display'),
    ]

    # InnovationRCAProjects are listed according to the sort order in the wagtail admin, and each InnovationRCAIndex lists only its subpages
    parent_page_types = ['rca.InnovationRCAIndex']

    search_name = 'InnovationRCA Project'

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        # Get related research
        projects = InnovationRCAProject.objects.filter(live=True).order_by('random_order')
        projects = projects.filter(project_type=self.project_type)

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
            areas=Area.objects.filter(slug='innovationrca'),
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
        SnippetChooserPanel('ad'),
    ]

class InnovationRCAIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.InnovationRCAIndex', 'intro'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.InnovationRCAIndex', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.InnovationRCAIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    indexed = False

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        # Get list of live projects
        projects = InnovationRCAProject.objects.filter(live=True, path__startswith=self.path)

        # Apply filters
        project_type = request.GET.get('project_type')
        current_past = request.GET.get('current_past')

        if current_past:
            current_past = current_past.lower()

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

        # order project subpages based on the sort order in the wagtail admin
        projects = projects.order_by('path')

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
    school = models.ForeignKey('taxonomy.School', null=True, blank=True, on_delete=models.SET_NULL, related_name='sustainrca_projects', help_text=help_text('rca.SustainRCAProject', 'school'))
    programme = models.ForeignKey('taxonomy.Programme', null=True, blank=True, on_delete=models.SET_NULL, related_name='sustainrca_projects', help_text=help_text('rca.SustainRCAProject', 'programme'))
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.SustainRCAProject', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.SustainRCAProject', 'show_on_homepage'))
    random_order = models.IntegerField(null=True, blank=True, editable=False)
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.SustainRCAProject', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + [
        index.SearchField('subtitle'),
        index.SearchField('description'),
        index.RelatedFields('school', [
            index.SearchField('display_name'),
        ]),
        index.RelatedFields('programme', [
            index.SearchField('display_name'),
        ]),
        index.SearchField('get_category_display'),
    ]

    search_name = 'SustainRCA Project'

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        # Get related research
        related_projects = SustainRCAProject.objects.live().order_by('random_order')
        related_projects = related_projects.filter(category=self.category)
        if self.programme:
            related_projects = related_projects.filter(programme=self.programme)
        elif self.school:
            related_projects = related_projects.filter(school=self.school)

        # Pagination
        paginator = Paginator(related_projects, 4)
        page = request.GET.get('page')
        try:
            related_projects = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            related_projects = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            related_projects = paginator.page(paginator.num_pages)

        if request.is_ajax() and 'pjax' not in request.GET:
            return render(request, "rca/includes/sustain_rca_listing.html", {
                'self': self,
                'projects': related_projects
            })
        else:
            return render(request, self.template, {
                'self': self,
                'projects': related_projects
            })

    def get_related_news(self, count=4):
        return NewsItem.get_related(
            areas=Area.objects.filter(slug='sustainrca'),
            programmes=Programme.objects.filter(id=self.programme_id) if self.programme else None,
            schools=School.objects.filter(id=self.school_id) if self.school else None,
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
        SnippetChooserPanel('ad'),
    ]

class SustainRCAIndex(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.SustainRCAIndex', 'intro'), blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.SustainRCAIndex', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.SustainRCAIndex', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    indexed = False

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        year = request.GET.get('year')
        category = request.GET.get('category')
        programme_slug = request.GET.get('programme')

        projects = SustainRCAProject.objects.live()

        # Year
        year_options = list(projects.order_by('-year').values_list('year', flat=True).distinct('year'))
        if year in year_options:
            projects = projects.filter(year=year)
        else:
            year = ''

        # Category
        available_categories = set(projects.values_list('category', flat=True))
        category_options = [c for c in zip(*SUSTAINRCA_CATEGORY_CHOICES)[0] if c in available_categories]
        if category in category_options:
            projects = projects.filter(category=category)
        else:
            category = ''

        # Programme
        programme_options = Programme.objects.filter(
            id__in=projects.values_list('programme', flat=True),
        )
        programme = programme_options.filter(slug=programme_slug).first()
        if programme:
            projects = projects.filter(programme=programme)

        # Pagination
        page = request.GET.get('page')
        paginator = Paginator(projects, 8)  # Show 8 projects per page
        try:
            projects = paginator.page(page)
        except PageNotAnInteger:
            projects = paginator.page(1)
        except EmptyPage:
            projects = paginator.page(paginator.num_pages)

        filters = [{
            "name": "year",
            "current_value": year,
            "options": year_options
        }, {
            "name": "category",
            "current_value": category,
            "options": category_options
        }, {
            "name": "programme",
            "current_value": programme.slug if programme else None,
            "options": [programme.slug for programme in programme_options]
        }]

        # Find template
        if request.is_ajax() and 'pjax' not in request.GET:
            template = "rca/includes/sustain_rca_listing.html"
        else:
            template = self.template

        # Render
        return render(request, template, {
            'self': self,
            'projects': projects,
            'years': year_options,
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
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.ReachOutRCAProject', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.ReachOutRCAProject', 'show_on_homepage'))
    project = models.CharField(max_length=255, choices=REACHOUT_PROJECT_CHOICES, help_text=help_text('rca.ReachOutRCAProject', 'project'))
    random_order = models.IntegerField(null=True, blank=True, editable=False)
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.ReachOutRCAProject', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    search_fields = Page.search_fields + [
        index.SearchField('subtitle'),
        index.SearchField('description'),
        index.SearchField('get_project_display'),
    ]

    search_name = 'ReachOutRCA Project'

    @vary_on_headers('X-Requested-With')
    def serve(self, request):
        # Get related research
        projects = ReachOutRCAProject.objects.filter(live=True).order_by('random_order')
        projects = projects.filter(project=self.project)

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
            areas=Area.objects.filter(slug='reachoutrca'),
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
        SnippetChooserPanel('ad'),
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
        SnippetChooserPanel('ad'),
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

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

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


# == Pathway page ==

class PathwayPageCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey('rca.PathwayPage', related_name='carousel_items')

class PathwayPageRelatedLink(Orderable, RelatedLinkMixin):
    page = ParentalKey('rca.PathwayPage', related_name='related_links')

class PathwayPageQuotation(Orderable):
    page = ParentalKey('rca.PathwayPage', related_name='quotations')
    quotation = models.TextField(help_text=help_text('rca.PathwayPageQuotation', 'quotation'))
    quotee = models.CharField(max_length=255, blank=True, help_text=help_text('rca.PathwayPageQuotation', 'quotee'))
    quotee_job_title = models.CharField(max_length=255, blank=True, help_text=help_text('rca.PathwayPageQuotation', 'quotee_job_title'))

    panels = [
        FieldPanel('quotation'),
        FieldPanel('quotee'),
        FieldPanel('quotee_job_title')
    ]

class PathwayPageRelatedDocument(Orderable):
    page = ParentalKey('rca.PathwayPage', related_name='documents')
    document = models.ForeignKey('wagtaildocs.Document', null=True, blank=True, related_name='+', help_text=help_text('rca.PathwayPageRelatedDocument', 'document'))
    document_name = models.CharField(max_length=255, help_text=help_text('rca.PathwayPageRelatedDocument', 'document_name'))

    panels = [
        DocumentChooserPanel('document'),
        FieldPanel('document_name')
    ]

class PathwayPageImage(Orderable):
    page = ParentalKey('rca.PathwayPage', related_name='images')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+', help_text=help_text('rca.PathwayPageImage', 'image'))

    panels = [
        ImageChooserPanel('image'),
    ]

class PathwayPageAd(Orderable):
    page = ParentalKey('rca.PathwayPage', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+', help_text=help_text('rca.PathwayPageAd', 'ad'))

    panels = [
        SnippetChooserPanel('ad'),
    ]

class PathwayPageReusableTextSnippet(Orderable):
    page = ParentalKey('rca.PathwayPage', related_name='reusable_text_snippets')
    reusable_text_snippet = models.ForeignKey('rca.ReusableTextSnippet', related_name='+', help_text=help_text('rca.PathwayPageReusableTextSnippet', 'reusable_text_snippet'))

    panels = [
        SnippetChooserPanel('reusable_text_snippet'),
    ]

class PathwayPageTag(TaggedItemBase):
    content_object = ParentalKey('rca.PathwayPage', related_name='tagged_items')

class PathwayPage(Page, SocialFields, SidebarBehaviourFields):
    intro = RichTextField(help_text=help_text('rca.PathwayPage', 'intro'), blank=True)
    body = RichTextField(help_text=help_text('rca.PathwayPage', 'body'))
    strapline = models.CharField(max_length=255, blank=True, help_text=help_text('rca.PathwayPage', 'strapline'))
    middle_column_body = RichTextField(blank=True, help_text=help_text('rca.PathwayPage', 'middle_column_body'))
    show_on_homepage = models.BooleanField(default=False, help_text=help_text('rca.PathwayPage', 'show_on_homepage'))
    twitter_feed = models.CharField(max_length=255, blank=True, help_text=help_text('rca.PathwayPage', 'twitter_feed', default=TWITTER_FEED_HELP_TEXT))
    related_school = models.ForeignKey('taxonomy.School', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.PathwayPage', 'related_school'))
    related_programme = models.ForeignKey('taxonomy.Programme', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.PathwayPage', 'related_programme'))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.PathwayPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))
    tags = ClusterTaggableManager(through=PathwayPageTag, help_text=help_text('rca.PathwayPage', 'tags'), blank=True)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    parent_page_types = ['rca.ProgrammePage']

    @property
    def search_name(self):
        if self.related_programme:
            return self.related_programme.display_name

        if self.related_school:
            return self.related_school.display_name

    content_panels = [
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

PathwayPage.promote_panels = [
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

PathwayPage.settings_panels = [
    PublishingPanel(),
    MultiFieldPanel([
        FieldPanel('collapse_upcoming_events'),
    ], 'Sidebar behaviour'),
]


# == Lightbox Gallery page ==

class LightBoxGalleryPageRelatedSchool(models.Model):
    page = ParentalKey('rca.LightBoxGalleryPage', related_name='related_schools')
    school = models.ForeignKey('taxonomy.School', on_delete=models.CASCADE, related_name='lightbox_pages', help_text=help_text('rca.LightboxGalleryPage', 'school'))

    api_fields = [
        'school',
    ]

    panels = [FieldPanel('school')]


class LightboxGalleryPageItem(Orderable):
    page = ParentalKey('rca.LightboxGalleryPage', related_name='gallery_items')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.LightboxGalleryPageItem', 'image'))
    embedly_url = models.URLField('Video URL', blank=True, help_text="A video to show instead of an image")
    poster_image = models.ForeignKey('rca.RcaImage', verbose_name="Video still image", null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text="A still image of the video to display when not playing.")

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('embedly_url'),
        ImageChooserPanel('poster_image'),
    ]


class LightboxGalleryPage(Page, SocialFields):
    intro = RichTextField(help_text=help_text('rca.LightboxGalleryPage', 'intro'), blank=True)
    listing_intro = models.CharField(max_length=100, blank=True, help_text=help_text('rca.LightboxGalleryPage', 'listing_intro', default="Used only on pages listing Lightbox Galleries"))
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('rca.StreamPage', 'feed_image', default="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio."))

    show_on_school_page = models.BooleanField(default=False, help_text=help_text('rca.LightboxGalleryPage', 'show_on_school_page'))

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

LightboxGalleryPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel('gallery_items', label="Gallery items"),
]

LightboxGalleryPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('show_on_school_page'),
        FieldPanel('listing_intro'),
        ImageChooserPanel('feed_image'),
        FieldPanel('search_description'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),

    InlinePanel('related_schools', label='Related schools'),
]


# == Redirects ==

class PageAlias(Page):
    alias = models.ForeignKey('wagtailcore.Page', null=True, blank=True, on_delete=models.SET_NULL, related_name='aliases')
    external_url = models.URLField("External link", null=True, blank=True)
    listing_intro = models.TextField(
        blank=True
    )
    feed_image = models.ForeignKey(
        'rca.RcaImage',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    def clean(self):
        if not self.alias and not self.external_url:
            raise ValidationError('You must specify an alias pointing to an existing page or external URL.')

    def serve(self, request):
        to = self.external_url if self.external_url else self.alias.url
        return redirect(to, permanent=False)

PageAlias.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('external_url'),
    PageChooserPanel('alias'),
]

PageAlias.promote_panels = Page.promote_panels + [
    MultiFieldPanel([
        FieldPanel('listing_intro'),
        ImageChooserPanel('feed_image'),
    ], "Cross-page behaviour",)
]


class EnquiryFormField(AbstractFormField):
    page = ParentalKey('EnquiryFormPage', related_name='form_fields')


class EnquiryFormBuilder(WagtailCaptchaFormBuilder):

    def get_field_options(self, field):
        options = super(EnquiryFormBuilder, self).get_field_options(field)

        if field.field_type == 'date':
            # Hobsons are expecting to receive emails with dates in a specific format.
            # On front-end we also have a date picker that uses this format.
            options['input_formats'] = ['%d/%m/%Y']

        return options


class EnquiryFormPage(WagtailCaptchaEmailForm):
    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)
    to_address_row = models.CharField(
        verbose_name='to address (rest of world)', max_length=255, blank=True,
        help_text="Optional - form submissions from the rest of the world will be emailed to these addresses (instead of the standard addresses). Separate multiple addresses by comma."
    )

    def __init__(self, *args, **kwargs):
        super(EnquiryFormPage, self).__init__(*args, **kwargs)

        # We need to set form builder here since wagtailcaptcha
        # sets it in __init__ too. We subclass it to override date
        # of birth format.
        self.form_builder = EnquiryFormBuilder

    def get_to_address(self, submission, form):
        # HACK: Work out whether they are in or out of the EU depending on the value of one of the fields
        # If they change the label of values of the field, you must update this!
        if form.cleaned_data['country-of-citizenship'] == u'Outside the European Union':
            return self.to_address_row

        return self.to_address

    def send_mail(self, form, to_address):
        addresses = [x.strip() for x in to_address.split(',')]

        content = ''
        for x in form.fields.items():
            if not isinstance(x[1], ReCaptchaField):  # exclude ReCaptchaField from notification
                content += '\n' + x[1].label + ': ' + unicode(form.data.get(x[0]))

        send_mail(self.subject, content, addresses, self.from_address)

    def process_form_submission(self, form):
        submission = FormSubmission.objects.create(
            form_data=json.dumps(form.cleaned_data, cls=DjangoJSONEncoder),
            page=self,
        )

        to_address = self.get_to_address(submission, form)
        if to_address:
            self.send_mail(form, to_address)

        return submission

    def get_template(self, request, *args, **kwargs):
        if request.is_ajax():
            return 'rca/enquiry_form_page_ajax.html'

        return super(EnquiryFormPage, self).get_template(request, *args, **kwargs)

    @vary_on_headers('X-Requested-With')
    def serve(self, request, *args, **kwargs):
        if request.method == 'POST':
            form = self.get_form(request.POST)

            if form.is_valid():
                self.process_form_submission(form)

                # render the landing_page
                # TODO: It is much better to redirect to it
                return render(
                    request,
                    self.landing_page_template,
                    self.get_context(request)
                )
        else:
            form = self.get_form()

        context = self.get_context(request)
        context['form'] = form
        return render(
            request,
            self.get_template(request, *args, **kwargs),
            context
        )

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('intro', classname="full"),
        FieldPanel('thank_you_text', classname="full"),
        FieldPanel('from_address'),
        FieldPanel('subject'),
        FieldPanel('to_address'),
        FieldPanel('to_address_row'),
        InlinePanel('form_fields', label="Form fields"),
    ]


@register_setting
class EnquiryFormSettings(BaseSetting):
    form_page = models.ForeignKey(Page, on_delete=models.SET_NULL, related_name='+', null=True, blank=True,
                                  help_text=help_text('rca.EnquiryFormSettings', 'form_page'))

    panels = [
        PageChooserPanel('form_page', page_type=EnquiryFormPage),
    ]


# == Snippet: DoubleclickCampaignManagerActivities ==
# Ticket: https://projects.torchbox.com/projects/rca-django-cms-project/tickets/898


class DoubleclickCampaignManagerActivities(models.Model):
    page = models.ForeignKey(Page, related_name='double_click', null=True, blank=True,
        help_text=help_text('rca.DoubleclickCampaignManagerActivities', 'page'))
    cat = models.CharField(max_length=255,
        help_text=help_text('rca.DoubleclickCampaignManagerActivities', 'cat'))

    panels = [
        PageChooserPanel('page'),
        FieldPanel('cat'),
    ]

    def __unicode__(self):
        return "{} -> {}".format(self.page.slug, self.cat)


register_snippet(DoubleclickCampaignManagerActivities)
