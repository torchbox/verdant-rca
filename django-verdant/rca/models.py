from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.shortcuts import render
from django.db.models import Min

from datetime import date

from core.models import Page, Orderable
from core.fields import RichTextField
from cluster.fields import ParentalKey

from verdantadmin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel, PageChooserPanel
from verdantimages.edit_handlers import ImageChooserPanel
from verdantimages.models import AbstractImage, AbstractRendition
from verdantdocs.edit_handlers import DocumentChooserPanel
from verdantsnippets.edit_handlers import SnippetChooserPanel
from verdantsnippets.models import register_snippet

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

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

    search_on_fields = ['title', 'creator', 'photographer']

    @property
    def default_alt_text(self):
        return self.alt

    def caption_lines(self):
        if self.creator:
            first_line = u"%s by %s" % (self.title, self.creator)
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
        ('visualcommunication', 'Visual Communication'),
        ('informationexperiencedesign', 'Information Experience Design'),
        ('designinteractions', 'Design Interactions'),
        ('designproducts', 'Design Products'),
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
        ('fashionmenswear', 'Fashion Menswear'),
        ('fashionwomenswear', 'Fashion Womenswear'),
        ('goldsmithingsilversmithingmetalworkjewellery', 'Goldsmithing, Silversmithing, Metalwork & Jewellery'),
        ('textiles', 'Textiles'),
        ('globalinnovationdesign', 'Global Innovation Design'),
    ),
}

ALL_PROGRAMMES = list(set([x for year_tuple in HISTORICAL_PROGRAMMES.values() for x in year_tuple]))

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
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+', help_text="The full bleed image in the background")
    head_of_school = models.ForeignKey('rca.StaffPage', null=True, blank=True, related_name='+')
    head_of_school_statement = RichTextField(null=True, blank=True)
    head_of_school_link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term")
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
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')

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
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')

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
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+', help_text="The full bleed image in the background")
    head_of_programme = models.ForeignKey('rca.StaffPage', null=True, blank=True, related_name='+', help_text="This is my help text")
    head_of_programme_statement = RichTextField(null=True, blank=True, help_text="This is my content this is my content this is my content")
    head_of_programme_link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    programme_video = models.CharField(max_length=255, blank=True)
    programme_video_poster_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternate Twitter handle, hashtag or search term")
    contact_title = models.CharField(max_length=255, blank=True)
    contact_address = models.TextField(blank=True)
    contact_link = models.URLField(blank=True)
    contact_link_text = models.CharField(max_length=255, blank=True)
    download_document_url = models.CharField(max_length=255, blank=True)
    download_document_text = models.CharField(max_length=255, blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term")
    facilities_text = RichTextField(null=True, blank=True)
    facilities_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    facilities_link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')

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
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term")
    subpage_types = ['NewsItem']

    def serve(self, request):
        programme = request.GET.get('programme')
        school = request.GET.get('school')
        area = request.GET.get('area')

        news = NewsItem.objects.filter(live=True, path__startswith=self.path)

        if programme and programme != '':
            news = news.filter(related_programmes__programme=programme)
        if school and school != '':
            news = news.filter(related_schools__school=school)
        if area and area != '':
            news = news.filter(area=area)

        news = news.order_by('-date')

        page = request.GET.get('page')
        paginator = Paginator(news, 10) # Show 10 news items per page
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
                'news': news
            })
        else:
            return render(request, self.template, {
                'self': self,
                'news': news
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


# == Event Item ==

class EventItemSpeaker(Orderable):
    page = ParentalKey('rca.EventItem', related_name='speakers')
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
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

class EventItemDatesTimes(Orderable):
    page = ParentalKey('rca.EventItem', related_name='dates_times')
    date_from = models.DateField("Start date")
    date_to = models.DateField("End date", null=True, blank=True, help_text="Not required if event is on a single day")
    time_from = models.CharField("Start time", max_length=255, blank=True)
    time_to = models.CharField("End time",max_length=255, blank=True)

    panels = [
        FieldPanel('date_from'),
        FieldPanel('date_to'),
        FieldPanel('time_from'),
        FieldPanel('time_to'),
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
    # TODO: Embargo Date, which would perhaps be part of a workflow module, not really a model thing?

    objects = models.Manager()
    future_objects = FutureEventItemManager()
    past_objects = PastEventItemManager()


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
        FieldPanel('eventbrite_id'),
        FieldPanel('external_link'),
        FieldPanel('external_link_text'),
        FieldPanel('middle_column_body')
    ], 'Event detail'),
    FieldPanel('body', classname="full"),
    InlinePanel(EventItem, 'dates_times', label="Dates and times"),
    InlinePanel(EventItem, 'speakers', label="Speaker"),
    InlinePanel(EventItem, 'carousel_items', label="Carousel content"),
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
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term")

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

        if period=='past':
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
        
        page = request.GET.get('page')
        paginator = Paginator(events, 10) # Show 10 events per page
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
                'events': events
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
    show_on_homepage = models.BooleanField()

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

class StandardPage(Page, SocialFields):
    intro = RichTextField(blank=True)
    body = RichTextField(blank=True)
    strapline = models.CharField(max_length=255, blank=True)
    middle_column_body = RichTextField(blank=True)
    show_on_homepage = models.BooleanField()

StandardPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('strapline', classname="full"),
    FieldPanel('intro', classname="full"),
    FieldPanel('body', classname="full"),
    InlinePanel(StandardPage, 'carousel_items', label="Carousel content"),
    InlinePanel(StandardPage, 'related_links', label="Related links"),
    FieldPanel('middle_column_body', classname="full"),
    InlinePanel(StandardPage, 'documents', label="Document"),
    InlinePanel(StandardPage, 'quotations', label="Quotation"),
    InlinePanel(StandardPage, 'images', label="Middle column image"),
    InlinePanel(StandardPage, 'manual_adverts', label="Manual adverts"),
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
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
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

class StandardIndexAd(Orderable):
    page = ParentalKey('rca.StandardIndex', related_name='manual_adverts')
    ad = models.ForeignKey('rca.Advert', related_name='+')

    panels = [
        SnippetChooserPanel('ad', Advert),
    ]

class StandardIndex(Page, SocialFields):
    intro = RichTextField(blank=True)
    intro_link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    strapline = models.CharField(max_length=255, blank=True)
    teasers_title = models.CharField(max_length=255, blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term")
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+', help_text="The full bleed image in the background")
    contact_title = models.CharField(max_length=255, blank=True)
    contact_address = models.TextField(blank=True)
    contact_link = models.URLField(blank=True)
    contact_link_text = models.CharField(max_length=255, blank=True)
    news_carousel_area = models.CharField(max_length=255, choices=AREA_CHOICES, blank=True)

StandardIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('strapline', classname="full"),
    MultiFieldPanel([
        FieldPanel('intro', classname="full"),
        PageChooserPanel('intro_link'),
    ],'Introduction'),
    InlinePanel(StandardIndex, 'carousel_items', label="Carousel content"),
    FieldPanel('teasers_title'),
    InlinePanel(StandardIndex, 'teasers', label="Teaser content"),
    InlinePanel(StandardIndex, 'related_links', label="Related links"),
    InlinePanel(StandardIndex, 'manual_adverts', label="Manual adverts"),
    FieldPanel('twitter_feed'),
    ImageChooserPanel('background_image'),
    MultiFieldPanel([
        FieldPanel('contact_title'),
        FieldPanel('contact_address'),
        FieldPanel('contact_link'),
        FieldPanel('contact_link_text'),
    ],'Contact'),
    InlinePanel(StandardIndex, 'contact_phone', label="Contact phone number"),
    InlinePanel(StandardIndex, 'contact_email', label="Contact email address"),
    FieldPanel('news_carousel_area'),
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
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+', help_text="The full bleed image in the background")
    news_item_1 = models.ForeignKey('core.Page', null=True, related_name='+')
    news_item_2 = models.ForeignKey('core.Page', null=True, related_name='+')
    packery_news = models.IntegerField("Number of news items to show", null=True, blank=True, choices=((1,1),(2,2),(3,3),(4,4),(5,5),))
    packery_staff = models.IntegerField("Number of staff to show", null=True, blank=True, choices=((1,1),(2,2),(3,3),(4,4),(5,5),))
    packery_student_work = models.IntegerField("Number of student work items to show", help_text="Student pages flagged to Show On Homepage must have at least one carousel item", null=True, blank=True, choices=((1,1),(2,2),(3,3),(4,4),(5,5),))
    packery_tweets = models.IntegerField("Number of tweets to show", null=True, blank=True, choices=((1,1),(2,2),(3,3),(4,4),(5,5),))
    packery_rcanow = models.IntegerField("Number of RCA Now items to show", null=True, blank=True, choices=((1,1),(2,2),(3,3),(4,4),(5,5),))
    packery_standard = models.IntegerField("Number of standard pages to show", null=True, blank=True, choices=((1,1),(2,2),(3,3),(4,4),(5,5),))

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
    download_info = models.ForeignKey('verdantdocs.Document', null=True, blank=True, related_name='+')
    listing_intro = models.CharField(max_length=255, help_text='Used only on pages listing jobs', blank=True)
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
    FieldPanel('description', classname="full"),
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
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term")

JobsIndex.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
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
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term")

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
    profile_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES)
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES)
    year = models.CharField(max_length=4, blank=True)
    intro = RichTextField(blank=True)
    listing_intro = models.CharField(max_length=100, help_text='Used only on pages displaying a list of pages of this type', blank=True)
    biography = RichTextField()
    show_on_homepage = models.BooleanField()

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
    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
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
    profile_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+')
    staff_type = models.CharField(max_length=255, blank=True, choices=STAFF_TYPES_CHOICES)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing this staff member's Twitter handle (or any hashtag or search term)")
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
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term")

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
    profile_image = models.ForeignKey('rca.RcaImage', related_name='+', null=True, blank=True)
    statement = RichTextField(blank=True)
    work_description = RichTextField(blank=True)
    work_type = models.CharField(max_length=255, choices=WORK_TYPES_CHOICES, blank=True)
    work_location = models.CharField(max_length=255, choices=CAMPUS_CHOICES, blank=True)
    work_awards = models.CharField(max_length=255, blank=True)
    student_twitter_feed = models.CharField(max_length=255, blank=True, help_text="Enter Twitter handle without @ symbol.")
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term")
    rca_content_id = models.CharField(max_length=255, blank=True) # for import
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    supervisor = models.ForeignKey('rca.StaffPage', related_name='+', null=True, blank=True)
    show_on_homepage = models.BooleanField()

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

class RcaNowPage(Page, SocialFields):
    body = RichTextField()
    author = models.CharField(max_length=255, blank=True)
    date = models.DateField("Creation date")
    programme = models.CharField(max_length=255, choices=PROGRAMME_CHOICES)
    school = models.CharField(max_length=255, choices=SCHOOL_CHOICES)
    area = models.CharField(max_length=255, choices=AREA_CHOICES)
    show_on_homepage = models.BooleanField()
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term")
    # TODO: tags

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
]


# == RCA Now index ==


class RcaNowIndex(Page, SocialFields):
    intro = RichTextField(blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term")

    def serve(self, request):
        programme = request.GET.get('programme')
        school = request.GET.get('school')
        area = request.GET.get('area')

        rca_now_items = RcaNowPage.objects.filter(live=True)

        if programme and programme != '':
            rca_now_items = rca_now_items.filter(programme=programme)
        if school and school != '':
            rca_now_items = rca_now_items.filter(school=school)
        if area and area != '':
            rca_now_items = rca_now_items.filter(area=area)

        rca_now_items = rca_now_items.order_by('-date')

        page = request.GET.get('page')
        paginator = Paginator(rca_now_items, 10) # Show 10 rca now items per page
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
                'rca_now_items': rca_now_items
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
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term")
    rca_content_id = models.CharField(max_length=255, blank=True) # for import
    eprintid = models.CharField(max_length=255, blank=True) # for import
    show_on_homepage = models.BooleanField()

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
    intro_link = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    teasers_title = models.CharField(max_length=255, blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term")
    background_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, related_name='+', help_text="The full bleed image in the background")
    contact_title = models.CharField(max_length=255, blank=True)
    contact_address = models.TextField(blank=True)
    contact_link = models.URLField(blank=True)
    contact_link_text = models.CharField(max_length=255, blank=True)
    news_carousel_area = models.CharField(max_length=255, choices=AREA_CHOICES, blank=True)

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
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term")

    def serve(self, request):
        research_type = request.GET.get('research_type')
        school = request.GET.get('school')
        theme = request.GET.get('theme')
        work_type = request.GET.get('work_type')

        research_items = ResearchItem.objects.filter(live=True)

        if research_type and research_type != '':
            research_items = research_items.filter(research_type=research_type)
        if school and school != '':
            research_items = research_items.filter(school=school)
        if theme and theme != '':
            research_items = research_items.filter(theme=theme)
        if work_type and work_type != '':
            research_items = research_items.filter(work_type=work_type)

        research_items.order_by('-year')

        page = request.GET.get('page')
        paginator = Paginator(research_items, 8) # Show 8 research items per page
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

class GalleryPage(Page, SocialFields):
    intro = RichTextField(blank=True)
    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternative Twitter handle, hashtag or search term")

GalleryPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    FieldPanel('twitter_feed'),
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
