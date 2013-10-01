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

    @property
    def default_alt_text(self):
        return self.alt

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
    ('openday', 'Open Day')
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
    ('theme1', 'Theme 1'),
    ('theme2', 'Theme 2'),
    ('themen', 'Theme N'),
)

SCHOOL_CHOICES = (
    ('schoolofarchitecture', 'School of Architecture'),
    ('schoolofcommunication', 'School of Communication'),
    ('schoolofdesign', 'School of Design'),
    ('schooloffineart', 'School of Fine Art'),
    ('schoolofhumanities', 'School of Humanities'),
    ('schoolofmaterial', 'School of Material'),
)

PROGRAMME_CHOICES = (
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
)

RESEARCH_TYPES_CHOICES = (
    ('student', 'Student'),
    ('staff', 'Staff'),
)

STAFF_TYPES_CHOICES = (
    ('academic', 'Academic'),
    ('technical','Technical'),
    ('administrative','Administrative'),
)

# Generic social fields abstract class to add social image/text to any new content type easily.
class SocialFields(models.Model):
    social_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    social_text = models.CharField(max_length=255, blank=True)

    class Meta:
        abstract = True

class CommonPromoteFields(models.Model):
    seo_title = models.CharField("Page title", max_length=255, blank=True, help_text="Optional. 'Search Engine Friendly' title. This will appear at the top of the browser window.")
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


# == Snippet: Advert ==
class Advert(models.Model):
    page = models.ForeignKey('core.Page', related_name='adverts', null=True, blank=True)
    url = models.URLField(null=True, blank=True)
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

class AdvertPlacement(models.Model):
    page = models.ForeignKey('core.Page', related_name='advert_placements')
    advert = models.ForeignKey('rca.Advert', related_name='+')


# == School page ==

class SchoolPageCarouselItem(CarouselItemFields):
    page = models.ForeignKey('rca.SchoolPage', related_name='carousel_items')

class SchoolPageContactTelEmail(models.Model):
    page = models.ForeignKey('rca.SchoolPage', related_name='contact_tel_email')
    phone_number = models.CharField(max_length=255, blank=True)
    email = models.CharField(max_length=255, blank=True)

    panels = [
        FieldPanel('phone_number'),
        FieldPanel('email'),
    ]

class SchoolPageRelatedLink(models.Model):
    page = models.ForeignKey('rca.SchoolPage', related_name='related_links')
    link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    link_text = models.CharField(max_length=255, help_text="Provide an alternate link title (default is target page's title)")

    panels = [
        PageChooserPanel('link'),
        FieldPanel('link_text'),
    ]

class SchoolPage(Page, SocialFields, CommonPromoteFields):
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+', help_text="The full bleed image in the background")
    head_of_school = models.ForeignKey('rca.StaffPage', null=True, blank=True, related_name='+')
    head_of_school_statement = RichTextField(null=True, blank=True)
    head_of_school_link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternate Twitter handle, hashtag or search term")
    contact_title = models.CharField(max_length=255, blank=True)
    contact_address = models.TextField(blank=True)
    contact_link = models.URLField(blank=True)
    contact_link_text = models.CharField(max_length=255, blank=True)
    head_of_research = models.ForeignKey('rca.StaffPage', null=True, blank=True, related_name='+')
    head_of_research_statement = RichTextField(null=True, blank=True)
    head_of_research_link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')

SchoolPage.content_panels = [
    FieldPanel('title', classname="full title"),
    ImageChooserPanel('background_image'),
    InlinePanel(SchoolPage, SchoolPageCarouselItem, label="Carousel content", help_text="test"),
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
    InlinePanel(SchoolPage, SchoolPageContactTelEmail, label="Contact phone numbers/emails"),
    PageChooserPanel('head_of_research', 'rca.StaffPage'),
    FieldPanel('head_of_research_statement', classname="full"),
    PageChooserPanel('head_of_research_link'),
    InlinePanel(SchoolPage, SchoolPageRelatedLink, fk_name='page', label="Related links"),
]

SchoolPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]


# == Programme page ==

class ProgrammePageCarouselItem(models.Model):
    page = models.ForeignKey('rca.ProgrammePage', related_name='carousel_items')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    text = models.CharField(max_length=255, help_text='This text will overlay the image', blank=True)
    url = models.URLField()

    panels = [
        ImageChooserPanel('image'), 
        FieldPanel('text'), 
        FieldPanel('url'),
    ]

class ProgrammePageRelatedLink(models.Model):
    page = models.ForeignKey('rca.ProgrammePage', related_name='related_links')
    link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    link_text = models.CharField(max_length=255, help_text="Provide an alternate link title (default is target page's title)")

    panels = [
        PageChooserPanel('link'),
        FieldPanel('link_text'),
    ]

class ProgrammePageOurSites(models.Model):
    page = models.ForeignKey('rca.ProgrammePage', related_name='our_sites')
    url = models.URLField()
    site_name = models.CharField(max_length=255)
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')

    panels = [
        ImageChooserPanel('image'), 
        FieldPanel('url'), 
        FieldPanel('site_name')
    ]

class ProgrammePageStudentStory(models.Model):
    page = models.ForeignKey('rca.ProgrammePage', related_name='student_stories')
    name = models.CharField(max_length=255)
    text = RichTextField()
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')

    panels = [
        FieldPanel('name'),
        FieldPanel('text'),
        ImageChooserPanel('image'),
        PageChooserPanel('link'),
    ]

class ProgrammePage(Page, SocialFields, CommonPromoteFields):
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES)
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES)
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+', help_text="The full bleed image in the background")
    head_of_programme = models.ForeignKey('rca.StaffPage', null=True, blank=True, related_name='+')
    head_of_programme_statement = RichTextField(null=True, blank=True)
    head_of_programme_link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    programme_video = models.CharField(max_length=255, blank=True)
    programme_video_poster_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    download_document_url = models.CharField(max_length=255, blank=True)
    download_document_text = models.CharField(max_length=255, blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternate Twitter handle, hashtag or search term")
    facilities_text = RichTextField(null=True, blank=True)
    facilities_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    facilities_link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')

    def tabbed_feature_count(self):
        count = 0;
        if self.programme_video:
            count = count + 1;
        if self.facilities_text or self.facilities_image:
            count = count + 1;
        if self.student_stories:
            count = count + 1;
        return count;

ProgrammePage.content_panels = [
    ImageChooserPanel('background_image'),
    FieldPanel('title', classname="full title"),
    InlinePanel(ProgrammePage, ProgrammePageCarouselItem, label="Carousel content"),
    InlinePanel(ProgrammePage, ProgrammePageRelatedLink, fk_name='page', label="Related links"),
    PageChooserPanel('head_of_programme', 'rca.StaffPage'),
    FieldPanel('head_of_programme_statement'),
    PageChooserPanel('head_of_programme_link'),
    InlinePanel(ProgrammePage, ProgrammePageOurSites, label="Our sites"),
    MultiFieldPanel([
        FieldPanel('programme_video'),
        ImageChooserPanel('programme_video_poster_image'),
    ], 'Video'),
    InlinePanel(ProgrammePage, ProgrammePageStudentStory, fk_name='page', label="Student stories"),
    MultiFieldPanel([
        ImageChooserPanel('facilities_image'),
        FieldPanel('facilities_text'),
        PageChooserPanel('facilities_link'),
    ], 'Facilities'),        
    FieldPanel('download_document_url'),
    FieldPanel('download_document_text'),
    FieldPanel('twitter_feed'),
]

ProgrammePage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
        FieldPanel('slug'),
    ], 'Common page configuration'),

    MultiFieldPanel([
        FieldPanel('show_in_menus'),
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),

    FieldPanel('school'),
    FieldPanel('programme'),
]


# == News Index ==

class NewsIndex(Page, CommonPromoteFields):
    subpage_types = ['NewsItem']


# == News Item ==

class NewsItemCarouselItem(CarouselItemFields):
    page = models.ForeignKey('rca.NewsItem', related_name='carousel_items')

class NewsItemLink(models.Model):
    page = models.ForeignKey('rca.NewsItem', related_name='related_links')
    link = models.URLField()
    link_text = models.CharField(max_length=255)

    panels=[
        FieldPanel('link'),
        FieldPanel('link_text')
    ]

class NewsItemRelatedSchool(models.Model):
    page = models.ForeignKey('rca.NewsItem', related_name='related_schools')
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True)

    panels = [
        FieldPanel('school')
    ]

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
    area = models.CharField(max_length=255, choices=AREA_CHOICES, blank=True)
    # TODO: Embargo Date, which would perhaps be part of a workflow module, not really a model thing?

    def feature_image(self):
        try:
            return self.carousel_items.filter(image__isnull=False)[0].image
        except IndexError:
            try:
                return self.carousel_items.filter(poster_image__isnull=False)[0].poster_image
            except IndexError:
                return None

    def get_related_news(self, count):
        # Assign each news item a score indicating similarity to this news item:
        # 100 points for a matching area, 10 points for a matching programme,
        # 1 point for a matching school.

        # if self.area is blank, we don't want to give priority to other news items
        # that also have a blank area field - so instead, set the target area to
        # something that will never match, so that it never contributes to the score
        my_area = self.area or "this_will_never_match"

        my_programmes = list(self.related_programmes.values_list('programme', flat=True))
        my_programmes.append("this_will_never_match_either")  # insert a dummy programme name to avoid an empty IN clause

        my_schools = list(self.related_schools.values_list('school', flat=True))
        my_schools.append("this_will_never_match_either")  # insert a dummy school name to avoid an empty IN clause

        return NewsItem.objects.extra(
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
            select_params=(my_area, tuple(my_programmes), tuple(my_schools))
        ).exclude(id=self.id).order_by('-score')[:count]


NewsItem.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('author'),
    FieldPanel('date'),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    InlinePanel(NewsItem, NewsItemLink, label="Links"),
    InlinePanel(NewsItem, NewsItemCarouselItem, label="Carousel content"),
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
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),

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

    panels=[
        FieldPanel('name'), 
        FieldPanel('surname'), 
        ImageChooserPanel('image'), 
        FieldPanel('link'),
    ]
    

class EventItemCarouselItem(models.Model):
    page = models.ForeignKey('rca.EventItem', related_name='carousel_items')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    embedly_url = models.URLField(blank=True)

    panels=[
        ImageChooserPanel('image'), 
        FieldPanel('embedly_url'),
    ]

class EventItemRelatedSchool(models.Model):
    page = models.ForeignKey('rca.EventItem', related_name='related_schools')
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True)

    panels = [FieldPanel('school')]

class EventItemRelatedProgramme(models.Model):
    page = models.ForeignKey('rca.EventItem', related_name='related_programmes')
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True)

    panels = [FieldPanel('programme')]

class EventItemDatesTimes(models.Model):
    page = models.ForeignKey('rca.EventItem', related_name='dates_times')
    date_from = models.DateField("Start date")
    date_to = models.DateField("End date", blank=True, help_text="Not required if event is on a single day")
    time_from = models.CharField("Start time", max_length=255, blank=True)
    time_to = models.CharField("End time",max_length=255, blank=True)

    panels = [
        FieldPanel('date_from'),
        FieldPanel('date_to'),
        FieldPanel('time_from'),
        FieldPanel('time_to'),
    ]

class EventItem(Page, SocialFields, CommonPromoteFields):
    body = RichTextField(blank=True)
    audience = models.CharField(max_length=255, choices=EVENT_AUDIENCE_CHOICES)
    location = models.CharField(max_length=255, choices=EVENT_LOCATION_CHOICES)
    location_other = models.CharField("'Other' location", max_length=255, blank=True)
    specific_directions = models.CharField(max_length=255, blank=True, help_text="Brief, more specific location e.g Go to reception on 2nd floor")
    specific_directions_link = models.URLField(blank=True)
    gallery = models.CharField(max_length=255, choices=EVENT_GALLERY_CHOICES, blank=True)
    cost = RichTextField(blank=True, help_text="Prices should be in bold")
    signup_link = models.URLField(blank=True)
    external_link = models.URLField(blank=True)
    external_link_text = models.CharField(max_length=255, blank=True)
    show_on_homepage = models.BooleanField()
    listing_intro = models.CharField(max_length=100, help_text='Used only on pages listing event items', blank=True)
    # TODO: Embargo Date, which would perhaps be part of a workflow module, not really a model thing?


EventItem.content_panels = [
    MultiFieldPanel([
        FieldPanel('title', classname="full title"),
        FieldPanel('audience'),
        FieldPanel('location'),
        FieldPanel('location_other'),
        FieldPanel('specific_directions'),
        FieldPanel('specific_directions_link'),
        FieldPanel('gallery'),
        FieldPanel('cost'),
        FieldPanel('signup_link'),
        FieldPanel('external_link'),
        FieldPanel('external_link_text'),
    ], 'Event detail'),
    FieldPanel('body', classname="full"),
    InlinePanel(EventItem, EventItemDatesTimes, label="Dates and times"),
    InlinePanel(EventItem, EventItemSpeaker, label="Speaker"),
    InlinePanel(EventItem, EventItemCarouselItem, label="Carousel content"),
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
    link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    link_text = models.CharField(max_length=255, help_text="Provide an alternate link title (default is target page's title)")

    panels = [
        PageChooserPanel('link'),
        FieldPanel('link_text'),
    ]

class StandardPageQuotation(models.Model):
    page = models.ForeignKey('rca.StandardPage', related_name='quotations')
    quotation = models.TextField()
    quotee = models.CharField(max_length=255, blank=True)
    quotee_job_title = models.CharField(max_length=255, blank=True)

class StandardPage(Page, SocialFields, CommonPromoteFields):
    intro = RichTextField(blank=True)
    body = RichTextField(blank=True)

StandardPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    InlinePanel(StandardPage, StandardPageCarouselItem, label="Carousel content"),
    InlinePanel(StandardPage, StandardPageRelatedLink, fk_name='page', label="Related links"),
    InlinePanel(StandardPage, StandardPageQuotation, label="Quotation"),
]

StandardPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
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

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('url'),
        FieldPanel('title', classname="full title"),
        FieldPanel('text'),
    ]

class StandardIndexRelatedLink(models.Model):
    page = models.ForeignKey('rca.StandardIndex', related_name='related_links')
    link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    link_text = models.CharField(max_length=255, help_text="Provide an alternate link title (default is target page's title)")

    panels = [
        PageChooserPanel('link'),
        FieldPanel('link_text'),
    ]

class StandardIndexContactPhone(models.Model):
    page = models.ForeignKey('rca.StandardIndex', related_name='contact_phone')
    phone_number = models.CharField(max_length=255)

    panels = [
        FieldPanel('phone_number')
    ]

class StandardIndexContactEmail(models.Model):
    page = models.ForeignKey('rca.StandardIndex', related_name='contact_email')
    email_address = models.CharField(max_length=255)

    panels = [
        FieldPanel('email_address')
    ]

class StandardIndex(Page, SocialFields, CommonPromoteFields):
    intro = RichTextField(blank=True)
    intro_link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    teasers_title = models.CharField(max_length=255, blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternate Twitter handle, hashtag or search term")
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+', help_text="The full bleed image in the background")
    contact_title = models.CharField(max_length=255, blank=True)
    contact_address = models.TextField(blank=True)
    contact_link = models.URLField(blank=True)
    contact_link_text = models.CharField(max_length=255, blank=True)
    news_carousel_area = models.CharField(max_length=255, choices=AREA_CHOICES, blank=True)

StandardIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    MultiFieldPanel([
        FieldPanel('intro'),
        PageChooserPanel('intro_link'),
    ],'Introduction'),
    InlinePanel(StandardIndex, StandardIndexCarouselItem, label="Carousel content"),
    FieldPanel('teasers_title'),
    InlinePanel(StandardIndex, StandardIndexTeaser, label="Teaser content"),
    InlinePanel(StandardIndex, StandardIndexRelatedLink, fk_name='page', label="Related links"),
    FieldPanel('twitter_feed'),
    ImageChooserPanel('background_image'),
    MultiFieldPanel([
        FieldPanel('contact_title'),
        FieldPanel('contact_address'),
        FieldPanel('contact_link'),
        FieldPanel('contact_link_text'),
        
    ],'Contact'),
    InlinePanel(StandardIndex, StandardIndexContactPhone, label="Contact phone number"),
    InlinePanel(StandardIndex, StandardIndexContactEmail, label="Contact email address"),
    FieldPanel('news_carousel_area'),
]

StandardIndex.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
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

class JobPageRelatedSchool(models.Model):
    page = models.ForeignKey('rca.JobPage', related_name='related_schools')
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True)

    panels = [FieldPanel('school')]

class JobPageRelatedProgramme(models.Model):
    page = models.ForeignKey('rca.JobPage', related_name='related_programmes')
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True)

    panels = [FieldPanel('programme')]

class JobPage(Page, SocialFields, CommonPromoteFields):
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True)
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES, blank=True, help_text="This is my hel text")
    other_department = models.CharField(max_length=255, blank=True)
    closing_date = models.DateField()
    interview_date = models.DateField(blank=True)
    responsible_to = models.CharField(max_length=255, blank=True)
    required_hours = models.CharField(max_length=255, blank=True)
    campus = models.CharField(max_length=255, choices=CAMPUS_CHOICES, blank=True)
    salary = models.CharField(max_length=255, blank=True)
    ref_number = models.CharField(max_length=255, blank=True)
    grade = models.CharField(max_length=255, blank=True)
    description = RichTextField()
    download_info = models.ForeignKey('verdantdocs.Document', null=True, blank=True, related_name='+')
    listing_intro = models.CharField(max_length=100, help_text='Used only on pages listing jobs', blank=True)
    show_on_homepage = models.BooleanField()

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
    FieldPanel('description'),
    DocumentChooserPanel('download_info'),
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
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]

   
# == Jobs index page ==

class JobsIndex(Page, SocialFields, CommonPromoteFields):
    pass
   

# == Staff profile page ==

class StaffPageRole(models.Model):
    page = models.ForeignKey('rca.StaffPage', related_name='roles')
    title = models.CharField(max_length=255)
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES)
    email = models.EmailField(max_length=255)

    panels = [
        FieldPanel('title'),
        FieldPanel('programme'),
        FieldPanel('email'),
    ]

class StaffPageCollaborations(models.Model):
    page = models.ForeignKey('rca.StaffPage', related_name='collaborations')
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

class StaffPagePublicationExhibition(models.Model):
    page = models.ForeignKey('rca.StaffPage', related_name='publications_exhibitions')
    title = models.CharField(max_length=255)
    typeof = models.CharField("Type", max_length=255, choices=[('publication', 'Publication'),('exhibition', 'Exhibition')])
    location_year = models.CharField("Location and year", max_length=255)
    authors_collaborators = models.TextField("Authors/collaborators", blank=True)
    link = models.URLField(blank=True)

    panels = [
        FieldPanel('title'),
        FieldPanel('typeof'),
        FieldPanel('location_year'),
        FieldPanel('authors_collaborators'),
        FieldPanel('link'),
    ]

class StaffPage(Page, SocialFields, CommonPromoteFields):
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES)
    profile_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    staff_type = models.CharField(max_length=255, blank=True, choices=STAFF_TYPES_CHOICES)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing this staff member's Twitter handle (or any hashtag or search term)")
    intro = RichTextField()
    biography = RichTextField()
    practice = RichTextField(blank=True)
    practice_link = models.URLField(blank=True)
    show_on_homepage = models.BooleanField()
    show_on_programme_page = models.BooleanField()
    listing_intro = models.CharField(max_length=100, help_text='Used only on pages displaying a list of pages of this type', blank=True)
    research_interests = RichTextField(blank=True)

StaffPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('school'),
    ImageChooserPanel('profile_image'),
    FieldPanel('staff_type'),
    InlinePanel(StaffPage, StaffPageRole, label="Roles"),
    FieldPanel('intro', classname="full"),
    FieldPanel('biography', classname="full"),
    FieldPanel('twitter_feed'),
    FieldPanel('research_interests', classname="full"),
    MultiFieldPanel([
        FieldPanel('practice'),
        FieldPanel('practice_link'),
    ], 'Practice'),
    InlinePanel(StaffPage, StaffPageCollaborations, label="Collaborations"),
    InlinePanel(StaffPage, StaffPagePublicationExhibition, label="Publications and Exhibitions"),
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
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks')
]
   
# == Student profile page ==

class StudentPageDegree(models.Model):
    page = models.ForeignKey('rca.StudentPage', related_name='degrees')
    degree = models.CharField(max_length=255)

    panels = [FieldPanel('degree')]

class StudentPageExhibition(models.Model):
    page = models.ForeignKey('rca.StudentPage', related_name='exhibitions')
    exhibition = models.CharField(max_length=255)

    panels = [FieldPanel('exhibition')]

class StudentPageExperience(models.Model):
    page = models.ForeignKey('rca.StudentPage', related_name='experiences')
    experience = models.CharField(max_length=255)

    panels = [FieldPanel('experience')]

class StudentPageAwards(models.Model):
    page = models.ForeignKey('rca.StudentPage', related_name='awards')
    award = models.CharField(max_length=255)

    panels = [FieldPanel('award')]

class StudentPageContacts(models.Model):
    page = models.ForeignKey('rca.StudentPage', related_name='contacts')
    email = models.EmailField(max_length=255, blank=True)
    phone = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)

    panels = [
        FieldPanel('email'),
        FieldPanel('phone'),
        FieldPanel('website'),
    ]

class StudentPageCarouselItem(CarouselItemFields):
    page = models.ForeignKey('rca.StudentPage', related_name='carousel_items')

class StudentPageWorkCollaborator(models.Model):
    page = models.ForeignKey('rca.StudentPage', related_name='collaborators')
    name = models.CharField(max_length=255)

    panels = [FieldPanel('name')]

class StudentPage(Page, SocialFields, CommonPromoteFields):
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES)
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES)
    current_degree = models.CharField(max_length=255)
    specialism = models.CharField(max_length=255, blank=True)
    profile_image = models.ForeignKey('rca.RcaImage', related_name='+')
    statement = RichTextField()
    project_title = models.CharField(max_length=255, blank=True)
    work_description = models.CharField(max_length=255, blank=True)
    work_type = models.CharField(max_length=255, choices=WORK_TYPES_CHOICES)
    work_location = models.CharField(max_length=255, choices=CAMPUS_CHOICES)
    work_awards = models.CharField(max_length=255)
    work_sponsors = models.CharField(max_length=255)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternate Twitter handle, hashtag or search term")

StudentPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('school'),
    FieldPanel('programme'),
    FieldPanel('current_degree'),
    ImageChooserPanel('profile_image'),
    InlinePanel(StudentPage, StudentPageDegree, label="Previous degrees"),
    InlinePanel(StudentPage, StudentPageExhibition, label="Exhibition"),
    InlinePanel(StudentPage, StudentPageExperience, label="Experience"),
    InlinePanel(StudentPage, StudentPageAwards, label="Awards"),
    FieldPanel('statement'),
    InlinePanel(StudentPage, StudentPageCarouselItem, label="Carousel content"),
    FieldPanel('project_title'),
    FieldPanel('work_description'),
    FieldPanel('work_type'),
    FieldPanel('work_location'),
    InlinePanel(StudentPage, StudentPageWorkCollaborator, label="Work collaborator"),
    FieldPanel('work_awards'),
    FieldPanel('work_sponsors'),
    FieldPanel('twitter_feed'),
]

StudentPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
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

# == RCA Now page ==

class RcaNowPagePageCarouselItem(CarouselItemFields):
    page = models.ForeignKey('rca.RcaNowPage', related_name='carousel_items')

class RcaNowPage(Page, SocialFields, CommonPromoteFields):
    body = RichTextField()
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES)
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES)
    area = models.CharField(max_length=255, choices=AREA_CHOICES)
    show_on_homepage = models.BooleanField()
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternate Twitter handle, hashtag or search term")
    # TODO: tags

RcaNowPage.content_panels = [
    InlinePanel(RcaNowPage, RcaNowPagePageCarouselItem, label="Carousel content"),
    FieldPanel('title', classname="full title"),
    FieldPanel('body', classname="full"),
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
    ], 'Cross-page behaviour'),

    MultiFieldPanel([
        ImageChooserPanel('social_image'),
        FieldPanel('social_text'),
    ], 'Social networks'),
]


# == RCA Now index ==

class RcaNowIndex(Page, SocialFields, CommonPromoteFields):
    pass

   
# == Research Item page ==

class ResearchItemCarouselItem(CarouselItemFields):
    page = models.ForeignKey('rca.ResearchItem', related_name='carousel_items')

class ResearchItemCreator(models.Model):
    page = models.ForeignKey('rca.ResearchItem', related_name='creator')
    person = models.ForeignKey('core.Page', null=True, blank=True, related_name='+', help_text="Choose an existing person's page, or enter a name manually below (which will not be linked).")
    manual_person_name= models.CharField(max_length=255, blank=True, help_text="Only required if the creator has no page of their own to link to")

class ResearchItemLink(models.Model):
    page = models.ForeignKey('rca.ResearchItem', related_name='links')
    link = models.URLField()
    link_text = models.CharField(max_length=255)

    panels=[
        FieldPanel('link'),
        FieldPanel('link_text')
    ]
class ResearchItem(Page, SocialFields, CommonPromoteFields):
    research_type = models.CharField(max_length=255, choices=RESEARCH_TYPES_CHOICES)
    ref = models.CharField(max_length=255, blank=True)
    year = models.CharField(max_length=4)
    description = RichTextField()
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES)
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES, blank=True)
    work_type = models.CharField(max_length=255, choices=WORK_TYPES_CHOICES)
    work_type_other = models.CharField("'Other' work type", max_length=255, blank=True)
    theme = models.CharField(max_length=255, choices=WORK_THEME_CHOICES)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternate Twitter handle, hashtag or search term")

ResearchItem.content_panels = [
    FieldPanel('title', classname="full title"),
    InlinePanel(ResearchItem, ResearchItemCarouselItem, label="Carousel content"),
    FieldPanel('research_type'),
    InlinePanel(ResearchItem, ResearchItemCreator, fk_name='page', label="Creator"),
    FieldPanel('ref'),
    FieldPanel('year'),
    FieldPanel('school'),
    FieldPanel('programme'),
    FieldPanel('work_type'),
    FieldPanel('work_type_other'),
    FieldPanel('theme'),
    FieldPanel('description'),
    InlinePanel(ResearchItem, ResearchItemLink, label="Links"),
    FieldPanel('twitter_feed'),
]

ResearchItem.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
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


# == Research Innovation page ==


class ResearchInnovationPageCarouselItem(CarouselItemFields):
    page = models.ForeignKey('rca.ResearchInnovationPage', related_name='carousel_items')

class ResearchInnovationPageTeaser(models.Model):
    page = models.ForeignKey('rca.ResearchInnovationPage', related_name='teasers')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    url = models.URLField(blank=True)
    title = models.CharField(max_length=255, blank=True)
    text = models.CharField(max_length=255, blank=True)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('url'),
        FieldPanel('title', classname="full title"),
        FieldPanel('text'),
    ]

class ResearchInnovationPageRelatedLink(models.Model):
    page = models.ForeignKey('rca.ResearchInnovationPage', related_name='related_links')
    link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    link_text = models.CharField(max_length=255, help_text="Provide an alternate link title (default is target page's title)")

    panels = [
        PageChooserPanel('link'),
        FieldPanel('link_text'),
    ]

class ResearchInnovationPageContactPhone(models.Model):
    page = models.ForeignKey('rca.ResearchInnovationPage', related_name='contact_phone')
    phone_number = models.CharField(max_length=255)

    panels = [
        FieldPanel('phone_number')
    ]

class ResearchInnovationPageContactEmail(models.Model):
    page = models.ForeignKey('rca.ResearchInnovationPage', related_name='contact_email')
    email_address = models.CharField(max_length=255)

    panels = [
        FieldPanel('email_address')
    ]

class ResearchInnovationPageCurrentResearch(models.Model):
    page = models.ForeignKey('rca.ResearchInnovationPage', related_name='current_research')
    link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')

    panels = [
        PageChooserPanel('link'),
    ]

class ResearchInnovationPage(Page, SocialFields, CommonPromoteFields):
    intro = RichTextField(blank=True)
    intro_link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    teasers_title = models.CharField(max_length=255, blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternate Twitter handle, hashtag or search term")
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+', help_text="The full bleed image in the background")
    contact_title = models.CharField(max_length=255, blank=True)
    contact_address = models.TextField(blank=True)
    contact_link = models.URLField(blank=True)
    contact_link_text = models.CharField(max_length=255, blank=True)
    news_carousel_area = models.CharField(max_length=255, choices=AREA_CHOICES, blank=True)

ResearchInnovationPage.content_panels = [
    FieldPanel('title', classname="full title"),
    MultiFieldPanel([
        FieldPanel('intro'),
        PageChooserPanel('intro_link'),
    ],'Introduction'),
    InlinePanel(ResearchInnovationPage, ResearchInnovationPageCurrentResearch, fk_name='page', label="Current research"),
    InlinePanel(ResearchInnovationPage, ResearchInnovationPageCarouselItem, label="Carousel content"),
    FieldPanel('teasers_title'),
    InlinePanel(ResearchInnovationPage, ResearchInnovationPageTeaser, label="Teaser content"),
    InlinePanel(ResearchInnovationPage, ResearchInnovationPageRelatedLink, fk_name='page', label="Related links"),
    FieldPanel('twitter_feed'),
    ImageChooserPanel('background_image'),
    MultiFieldPanel([
        FieldPanel('contact_title'),
        FieldPanel('contact_address'),
        FieldPanel('contact_link'),
        FieldPanel('contact_link_text'),
        
    ],'Contact'),
    InlinePanel(ResearchInnovationPage, ResearchInnovationPageContactPhone, label="Contact phone number"),
    InlinePanel(ResearchInnovationPage, ResearchInnovationPageContactEmail, label="Contact email address"),
    FieldPanel('news_carousel_area'),
]

ResearchInnovationPage.promote_panels = [
    MultiFieldPanel([
        FieldPanel('seo_title'),
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

   
# == Current research page ==

class CurrentResearchPage(Page, SocialFields, CommonPromoteFields):
    pass

   
# == Gallery Page ==

class GalleryPage(Page, SocialFields, CommonPromoteFields):
    pass

   
# == Contact Us page ==

class ContactUsPage(Page, SocialFields, CommonPromoteFields):
    pass
