from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.shortcuts import render

from core.models import Page
from core.fields import RichTextField

from verdantadmin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel, RichTextFieldPanel, PageChooserPanel
from verdantimages.edit_handlers import ImageChooserPanel
from verdantimages.models import AbstractImage, AbstractRendition
from verdantdocs.edit_handlers import DocumentChooserPanel
from verdantsnippets.models import register_snippet

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

# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(pre_delete, sender=RcaImage)
def image_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)

class RcaRendition(AbstractRendition):
    image = models.ForeignKey('RcaImage', related_name='renditions')

# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(pre_delete, sender=RcaRendition)
def rendition_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)


NEWS_AREA_CHOICES = (
    ('helenhamlyn', 'Helen Hamlyn'),
    ('innovationrca', 'InnovationRCA'),
    ('research', 'Research'),
    ('knowledgeexchange', 'Knowledge Exchange'),
    ('showrca', 'Show RCA'),
    ('fuelrca', 'Fuel RCA'),
)

EVENT_AUDIENCE_CHOICES = (
    ('public', 'Public'),
    ('rcaonly', 'RCA only'),
)

EVENT_LOCATION_CHOICES = (
    ('kensington', 'Kensington'),
    ('battersea', 'Battersea'),
    ('other', 'Other (enter below)')
)

EVENT_GALLERY_CHOICES = (
    ('gallery1', 'Gallery 1'),
    ('gallery2', 'Gallery 2'),
    ('galleryn', 'Gallery N'),
)

WORK_TYPES_CHOICES = (
    ('gallery1', 'Gallery 1'),
    ('gallery2', 'Gallery 2'),
    ('galleryn', 'Gallery N'),
)

SCHOOL_CHOICES = (
    ('school1', 'School 1'),
    ('school2', 'School 2'),
    ('schooln', 'School N'),
)

PROGRAMME_CHOICES = (
    ('programme1', 'Programme 1'),
    ('programme2', 'Programme 2'),
    ('programmen', 'Programme N'),
)


# Generic social fields abstract class to add social image/text to any new content type easily.
class SocialFields(models.Model):
    social_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    social_text = models.CharField(max_length=255, blank=True)

    class Meta:
        abstract = True

class CommonPromoteFields(models.Model):
    show_in_menus = models.BooleanField(default=False, help_text="Whether a link to this page will appear in automatically generated menus")

    class Meta:
        abstract = True

# Carousel item abstract class - all carousels basically require the same fields
class CarouselItemFields(models.Model):
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    overlay_text = models.CharField(max_length=255, blank=True)
    link = models.URLField(blank=True)
    embedly_url = models.URLField(blank=True)
    poster_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')

    panels=[
        ImageChooserPanel('image'), 
        FieldPanel('overlay_text'),
        FieldPanel('link'),
        FieldPanel('embedly_url'),
        ImageChooserPanel('poster_image'), 
    ]

    class Meta:
        abstract = True


# == School ==

class SchoolPage(Page, CommonPromoteFields):
    """
    School page (currently only necessary for foreign key with ProgrammePage)
    """
    pass


# == Programme page ==

class ProgrammePageCarouselItem(models.Model):
    page = models.ForeignKey('rca.ProgrammePage', related_name='carousel_items')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    text = models.CharField(max_length=255, help_text='This text will overlay the image', blank=True)
    url = models.URLField()

class ProgrammePageRelatedLink(models.Model):
    page = models.ForeignKey('rca.ProgrammePage', related_name='related_links')
    url = models.URLField()
    link_text = models.CharField(max_length=255)

class ProgrammePageOurSites(models.Model):
    page = models.ForeignKey('rca.ProgrammePage', related_name='our_sites')
    url = models.URLField()
    site_name = models.CharField(max_length=255)
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')

class ProgrammePageStudentStory(models.Model):
    page = models.ForeignKey('rca.ProgrammePage', related_name='student_stories')
    name = models.CharField(max_length=255)
    text = RichTextField()
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')

class ProgrammePageFacilities(models.Model):
    page = models.ForeignKey('rca.ProgrammePage', related_name='facilities')
    text = RichTextField()
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')

class ProgrammePage(Page, CommonPromoteFields):
    head_of_programme = models.CharField(max_length=255)
    head_of_programme_statement = RichTextField()
    programme_video = models.CharField(max_length=255, blank=True)
    download_document_url = models.CharField(max_length=255, blank=True)
    download_document_text = models.CharField(max_length=255, blank=True)

ProgrammePage.content_panels = [
    InlinePanel(ProgrammePage, ProgrammePageCarouselItem, label="Carousel content", 
        panels=[ImageChooserPanel('image'), FieldPanel('text'), FieldPanel('url')]
    ),
    InlinePanel(ProgrammePage, ProgrammePageRelatedLink, label="Related links"),
    FieldPanel('head_of_programme'),
    RichTextFieldPanel('head_of_programme_statement'),
    InlinePanel(ProgrammePage, ProgrammePageOurSites, label="Our sites",
        panels=[ImageChooserPanel('image'), FieldPanel('url'), FieldPanel('site_name')]
    ),
    FieldPanel('programme_video'),
    InlinePanel(ProgrammePage, ProgrammePageStudentStory, label="Student stories"),
    InlinePanel(ProgrammePage, ProgrammePageFacilities, label="Facilities"),        
    FieldPanel('download_document_url'),
    FieldPanel('download_document_text'),
]

ProgrammePage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),
]


# == News Index ==

class NewsIndex(Page, CommonPromoteFields):
    subpage_types = ['NewsItem']


# == News Item ==

class NewsItemCarouselItem(CarouselItemFields):
    page = models.ForeignKey('rca.NewsItem', related_name='carousel_items')

class NewsItemRelatedLink(models.Model):
    page = models.ForeignKey('rca.NewsItem', related_name='related_links')
    url = models.URLField()
    link_text = models.CharField(max_length=255)

class NewsItemRelatedSchool(models.Model):
    page = models.ForeignKey('rca.NewsItem', related_name='related_schools')
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True)

    panels = [FieldPanel('school')]

class NewsItemRelatedProgramme(models.Model):
    page = models.ForeignKey('rca.NewsItem', related_name='related_programmes')
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True)

    panels = [FieldPanel('programme')]

class NewsItem(Page, SocialFields, CommonPromoteFields):
    author = models.CharField(max_length=255)
    date = models.DateField()
    intro = RichTextField()
    body = RichTextField()
    show_on_homepage = models.BooleanField()
    listing_intro = models.CharField(max_length=100, help_text='Used only on pages listing news items', blank=True)
    area = models.CharField(max_length=255, choices=NEWS_AREA_CHOICES, blank=True)
    # TODO: Embargo Date, which would perhaps be part of a workflow module, not really a model thing?

NewsItem.content_panels = [
    FieldPanel('author'),
    FieldPanel('date'),
    RichTextFieldPanel('intro'),
    RichTextFieldPanel('body'),
    InlinePanel(NewsItem, NewsItemRelatedLink, label="Related links",
        panels=[FieldPanel('url'), FieldPanel('link_text')]
    ),
    InlinePanel(NewsItem, NewsItemCarouselItem, label="Carousel content"),
]

NewsItem.promote_panels = [
     MultiFieldPanel([
        FieldPanel('title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),
    ImageChooserPanel('social_image'),
    FieldPanel('social_text'),
    FieldPanel('show_on_homepage'),
    FieldPanel('listing_intro'),
    FieldPanel('area'),
    InlinePanel(NewsItem, NewsItemRelatedSchool, label="Related schools"),
    InlinePanel(NewsItem, NewsItemRelatedProgramme, label="Related programmes"),
]


# == Event Item ==

class EventItemSpeaker(models.Model):
    page = models.ForeignKey('rca.EventItem', related_name='speakers')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)
    link = models.URLField()

class EventItemCarouselItem(models.Model):
    page = models.ForeignKey('rca.EventItem', related_name='carousel_items')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    embedly_url = models.URLField(blank=True)

class EventItemRelatedSchool(models.Model):
    page = models.ForeignKey('rca.EventItem', related_name='related_schools')
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True)

    panels = [FieldPanel('school')]

class EventItemRelatedProgramme(models.Model):
    page = models.ForeignKey('rca.EventItem', related_name='related_programmes')
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True)

    panels = [FieldPanel('programme')]

class EventItem(Page, SocialFields, CommonPromoteFields):
    date_to = models.DateField()
    date_from = models.DateField()
    times = RichTextField(blank=True)
    audience = models.CharField(max_length=255, choices=EVENT_AUDIENCE_CHOICES)
    location = models.CharField(max_length=255, choices=EVENT_LOCATION_CHOICES)
    location_other = models.CharField("'Other' location", max_length=255, blank=True)
    specific_directions = models.CharField(max_length=255, blank=True, help_text="Brief, more specific location e.g Go to reception on 2nd floor")
    specific_directions_link = models.URLField(blank=True)
    gallery = models.CharField(max_length=255, choices=EVENT_GALLERY_CHOICES)
    cost = RichTextField(blank=True)
    signup_link = models.URLField(blank=True)
    external_link = models.URLField(blank=True)
    external_link_text = models.CharField(max_length=255, blank=True)
    show_on_homepage = models.BooleanField()
    listing_intro = models.CharField(max_length=100, help_text='Used only on pages listing event items', blank=True)
    # TODO: Embargo Date, which would perhaps be part of a workflow module, not really a model thing?

EventItem.content_panels = [
    MultiFieldPanel([
        FieldPanel('date_to'),
        FieldPanel('date_from'),
        RichTextFieldPanel('times'),
        FieldPanel('audience'),
        FieldPanel('location'),
        FieldPanel('location_other'),
        FieldPanel('specific_directions'),
        FieldPanel('specific_directions_link'),
        FieldPanel('gallery'),
        RichTextFieldPanel('cost'),
        FieldPanel('signup_link'),
        FieldPanel('external_link'),
        FieldPanel('external_link_text'),
    ], 'Event detail'),
    InlinePanel(EventItem, EventItemSpeaker, label="Speaker",
        panels=[FieldPanel('name'), FieldPanel('surname'), ImageChooserPanel('image'), FieldPanel('link')]
    ),
    InlinePanel(EventItem, EventItemCarouselItem, label="Carousel content",
        panels=[ImageChooserPanel('image'), FieldPanel('embedly_url')]
    ),
]

EventItem.promote_panels = [
    MultiFieldPanel([
        FieldPanel('title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
        FieldPanel('show_on_homepage'),
        FieldPanel('listing_intro'),
    ], 'Cross-page behaviour'),
    
    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
   
    InlinePanel(EventItem, EventItemRelatedSchool, label="Related schools"),
    InlinePanel(EventItem, EventItemRelatedProgramme, label="Related programmes"),
]


# == Standard page ==

class StandardPageCarouselItem(CarouselItemFields):
    page = models.ForeignKey('rca.StandardPage', related_name='carousel_items')

class StandardPageRelatedLink(models.Model):
    page = models.ForeignKey('rca.StandardPage', related_name='related_links')
    url = models.URLField()
    link_text = models.CharField(max_length=255)

class StandardPage(Page, SocialFields, CommonPromoteFields):
    intro = RichTextField(blank=True)
    body = RichTextField(blank=True)

StandardPage.content_panels = [
    RichTextFieldPanel('intro'),
    RichTextFieldPanel('body'),
    InlinePanel(StandardPage, StandardPageCarouselItem, label="Carousel content"),
    InlinePanel(StandardPage, StandardPageRelatedLink, label="Related links"),
]

StandardPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]

   
# == Standard Index page ==

class StandardIndexCarouselItem(CarouselItemFields):
    page = models.ForeignKey('rca.StandardIndex', related_name='carousel_items')

class StandardIndexTeaser(models.Model):
    page = models.ForeignKey('rca.StandardIndex', related_name='teasers')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    url = models.URLField(blank=True)
    title = models.CharField(max_length=255, blank=True)
    text = models.CharField(max_length=255, blank=True)

class StandardIndexRelatedLink(models.Model):
    page = models.ForeignKey('rca.StandardIndex', related_name='related_links')
    link = models.ForeignKey('rca.StandardPage', null=True, blank=True, related_name='related_links_link')

    panel = [
        PageChooserPanel('link'),
    ]

class StandardIndex(Page, SocialFields, CommonPromoteFields):
    teasers_title = models.CharField(max_length=255, blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True)


StandardIndex.content_panels = [
    InlinePanel(StandardIndex, StandardIndexCarouselItem, label="Carousel content"),
    MultiFieldPanel([
        FieldPanel('teasers_title'),
        InlinePanel(StandardIndex, StandardIndexTeaser, label="Teaser content"),
    ],'Teasers'),
    InlinePanel(StandardIndex, StandardIndexRelatedLink, label="Related links"),
]

StandardIndex.promote_panels = [
    MultiFieldPanel([
        FieldPanel('title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]


# == Home page ==

class HomePage(Page, SocialFields, CommonPromoteFields):
    pass


# == Job page ==

class JobPage(Page, SocialFields, CommonPromoteFields):
    pass

   
# == Jobs index page ==

class JobsIndex(Page, SocialFields, CommonPromoteFields):
    pass
   

# == Staff profile page ==

class StaffPage(Page, SocialFields, CommonPromoteFields):
    pass

   
# == Student profile page ==

class StudentPage(Page, SocialFields, CommonPromoteFields):
    pass


# == RCA Now page ==

class RcaNowPage(Page, SocialFields, CommonPromoteFields):
    pass

   
# == RCA Now index ==

class RcaNowIndex(Page, SocialFields, CommonPromoteFields):
    pass

   
# == Research Item page ==

class ResearchItem(Page, SocialFields, CommonPromoteFields):
    pass


# == Research Innovation page ==

class ResearchInnovationPage(Page, SocialFields, CommonPromoteFields):
    pass

   
# == Current research page ==

class CurrentResearchPage(Page, SocialFields, CommonPromoteFields):
    pass

   
# == Gallery Page ==

class GalleryPage(Page, SocialFields, CommonPromoteFields):
    pass

   
# == Contact Us page ==

class ContactUsPage(Page, SocialFields, CommonPromoteFields):
    pass


# == Snippet: Advert ==
class Advert(models.Model):
    page = models.ForeignKey('core.Page', related_name='adverts')
    url = models.URLField()
    text = models.CharField(max_length=255)
    show_globally = models.BooleanField(default=False)

    panels = [
        PageChooserPanel('page'),
        FieldPanel('url'),
        FieldPanel('text'),
        FieldPanel('show_globally'),
    ]

    def __unicode__(self):
        return self.text

register_snippet(Advert)
