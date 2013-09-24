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


# DO NOT USE THIS FOR REAL CONTENT TYPE MODELS
class RelatedLink(models.Model):
    page = models.ForeignKey('core.Page', related_name='generic_related_links')
    url = models.URLField()
    link_text = models.CharField(max_length=255)

    # let's allow related links to have their own images. Just for kicks.
    # (actually, it's so that we can check that the widget override for ImageChooserPanel happens
    # within formsets too)
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')

# DO NOT USE THIS FOR REAL CONTENT TYPE MODELS
class RelatedDocument(models.Model):
    page = models.ForeignKey('core.Page', related_name='related_documents')
    document = models.ForeignKey('verdantdocs.Document', null=True, blank=True, related_name='+')

    panels = [
        DocumentChooserPanel('document')
    ]

# DO NOT USE THIS FOR REAL CONTENT TYPE MODELS: not sure of it's purpose
class EditorialPage(Page):
    body = RichTextField()

    # Setting a class as 'abstract' indicates that it's only intended to be a parent
    # type for more specific page types, and shouldn't be used directly;
    # it will thus be excluded from the list of page types a superuser can create.
    #
    # (NB it still gets a database table behind the scenes, so it isn't abstract
    # by Django's own definition)
    is_abstract = True


# Examples to be copied and pasted:
#  InlinePanel(Page, RelatedLink, label="Wonderful related links",
#     # label is optional - we'll derive one from the related_name of the relation if not specified
#     # Could also pass a panels=[...] argument here if we wanted to customise the display of the inline sub-forms
#     panels=[FieldPanel('url'), FieldPanel('link_text'), ImageChooserPanel('image')]
# ),


# Everything that follows is 'real' template code to be used in the actual RCA site, rather than just verdant testing purposes

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


# Generic social fields abstract class to add social image/text to any new content type easily.
class SocialFields(models.Model):
    social_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    social_text = models.CharField(max_length=255, blank=True)

    class Meta:
        abstract = True

# Carousel item abstract class - all carousels basically require the same fields
class CarouselItemFields(models.Model):
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    image_year = models.CharField(max_length=25, blank=True)
    image_creator = models.CharField(max_length=255, blank=True)
    image_medium = models.CharField(max_length=255, blank=True)
    image_dimensions = models.CharField(max_length=25, blank=True)
    image_photographer = models.CharField(max_length=25, blank=True)
    overlay_text = models.CharField(max_length=255, blank=True)
    link = models.URLField(blank=True)
    embedly_url = models.URLField(blank=True)
    poster_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')

    panels=[
        ImageChooserPanel('image'), 
        FieldPanel('image_year'), 
        FieldPanel('image_creator'), 
        FieldPanel('image_medium'), 
        FieldPanel('image_dimensions'),
        FieldPanel('image_photographer'),
        FieldPanel('overlay_text'),
        FieldPanel('link'),
        FieldPanel('embedly_url'),
        ImageChooserPanel('poster_image'), 
    ]

    class Meta:
        abstract = True


# == Authors Index ==

class AuthorsIndex(Page):
    subpage_types = ['AuthorPage']


# == Author Page ==

class AuthorPage(EditorialPage):
    mugshot = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')

    def serve(self, request):
        news_items = self.news_items.order_by('title')

        return render(request, self.template, {
            'self': self,
            'news_items': news_items,
        })

AuthorPage.content_panels = [
    ImageChooserPanel('mugshot'),
    RichTextFieldPanel('body'),
]

AuthorPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),
]


# == School ==

class SchoolPage(Page):
    """
    School page (currently only necessary for foreign key with ProgrammePage)
    """
    pass


# == Programme page ==

class ProgrammePageCarouselItem(models.Model):
    page = models.ForeignKey('rca.ProgrammePage', related_name='carousel_items')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    text = models.CharField(max_length=25, help_text='This text will overlay the image', blank=True)
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

class ProgrammePage(Page):
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

class NewsIndex(Page):
    subpage_types = ['NewsItem']


# == News Item ==

class NewsItemCarouselItem(CarouselItemFields):
    page = models.ForeignKey('rca.NewsItem', related_name='carousel_items')

class NewsItemRelatedLink(models.Model):
    page = models.ForeignKey('rca.NewsItem', related_name='related_links')
    url = models.URLField()
    link_text = models.CharField(max_length=255)

class NewsItem(Page, SocialFields):
    author = models.ForeignKey('rca.AuthorPage', null=True, blank=True, related_name='news_items')
    date = models.DateField()
    intro = RichTextField()
    body = RichTextField()
    show_on_homepage = models.BooleanField()
    listing_intro = models.CharField(max_length=100, help_text='Used only on pages listing news items', blank=True)
    area = models.CharField(max_length=255, choices=NEWS_AREA_CHOICES, blank=True)
    related_school = models.ForeignKey('rca.SchoolPage', null=True, blank=True, related_name='news_item')
    related_programme = models.ForeignKey('rca.ProgrammePage', null=True, blank=True, related_name='news_item')
    # TODO: Embargo Date, which would perhaps be part of a workflow module, not really a model thing?

NewsItem.content_panels = [
    PageChooserPanel('author', AuthorPage),
    FieldPanel('date'),
    RichTextFieldPanel('intro'),
    RichTextFieldPanel('body'),
    InlinePanel(NewsItem, NewsItemRelatedLink, label="Related links",
        panels=[PageChooserPanel('url'), FieldPanel('link_text')]
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
    PageChooserPanel('related_school', SchoolPage),
    PageChooserPanel('related_programme', ProgrammePage),
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

class EventItem(Page, SocialFields):
    date_to = models.DateField()
    date_from = models.DateField()
    times = RichTextField(blank=True)
    audience = models.CharField(max_length=255, choices=EVENT_AUDIENCE_CHOICES)
    location = models.CharField(max_length=255, choices=EVENT_LOCATION_CHOICES)
    specific_directions = models.CharField(max_length=255, blank=True, help_text="Brief, more specific location e.g Go to reception on 2nd floor")
    specific_directions_link = models.URLField(blank=True)
    gallery = models.CharField(max_length=255, choices=EVENT_GALLERY_CHOICES)
    cost = RichTextField(blank=True)
    signup_link = models.URLField(blank=True)
    # TODO: Event URL, purpose unknown
    show_on_homepage = models.BooleanField()
    related_school = models.ForeignKey('rca.SchoolPage', null=True, blank=True, related_name='event_item')
    related_programme = models.ForeignKey('rca.ProgrammePage', null=True, blank=True, related_name='event_item')
    listing_intro = models.CharField(max_length=100, help_text='Used only on pages listing event items', blank=True)
    # TODO: Embargo Date, which would perhaps be part of a workflow module, not really a model thing?

EventItem.content_panels = [
    FieldPanel('date_to'),
    FieldPanel('date_from'),
    RichTextFieldPanel('times'),
    FieldPanel('audience'),
    FieldPanel('location'),
    FieldPanel('specific_directions'),
    FieldPanel('specific_directions_link'),
    FieldPanel('gallery'),
    RichTextFieldPanel('cost'),
    FieldPanel('signup_link'),
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
    ImageChooserPanel('social_image'),
    FieldPanel('social_text'),
    FieldPanel('show_on_homepage'),
    FieldPanel('listing_intro'),
    PageChooserPanel('related_school', SchoolPage),
    PageChooserPanel('related_programme', ProgrammePage),
]


# == Standard page ==

class StandardPageCarouselItem(CarouselItemFields):
    page = models.ForeignKey('rca.StandardPage', related_name='carousel_items')

class StandardPageRelatedLink(models.Model):
    page = models.ForeignKey('rca.StandardPage', related_name='related_links')
    url = models.URLField()
    link_text = models.CharField(max_length=255)

class StandardPage(Page, SocialFields):
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
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]

   
# == Standard Index page ==

class StandardIndex(Page, SocialFields):
    pass


# == Home page ==

class HomePage(Page, SocialFields):
    pass


# == Job page ==

class JobPage(Page, SocialFields):
    pass

   
# == Jobs index page ==

class JobsIndex(Page, SocialFields):
    pass
   

# == Staff profile page ==

class StaffPage(Page, SocialFields):
    pass

   
# == Student profile page ==

class StudentPage(Page, SocialFields):
    pass


# == RCA Now page ==

class RcaNowPage(Page, SocialFields):
    pass

   
# == RCA Now index ==

class RcaNowIndex(Page, SocialFields):
    pass

   
# == Research Item page ==

class ResearchItem(Page, SocialFields):
    pass


# == Research Innovation page ==

class ResearchInnovationPage(Page, SocialFields):
    pass

   
# == Current research page ==

class CurrentResearchPage(Page, SocialFields):
    pass

   
# == Gallery Page ==

class GalleryPage(Page, SocialFields):
    pass

   
# == Contact Us page ==

class ContactUsPage(Page, SocialFields):
    pass

