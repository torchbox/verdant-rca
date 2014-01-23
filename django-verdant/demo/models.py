from django.db import models
from core.models import Page, Orderable
from core.fields import RichTextField
from cluster.fields import ParentalKey

from verdantadmin.edit_handlers import FieldPanel, MultiFieldPanel, InlinePanel, PageChooserPanel
from verdantimages.edit_handlers import ImageChooserPanel
from verdantimages.models import AbstractImage, AbstractRendition
from verdantdocs.edit_handlers import DocumentChooserPanel
from verdantsnippets.edit_handlers import SnippetChooserPanel

from cluster.tags import ClusterTaggableManager
from taggit.models import TaggedItemBase

from django.shortcuts import render

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


EVENT_AUDIENCE_CHOICES = (
    ('public', "Public"),
    ('private', "Private"),
)


COMMON_PANELS = (
    FieldPanel('slug'),
    FieldPanel('seo_title'),
    FieldPanel('show_in_menus'),
    ImageChooserPanel('feed_image'),
    FieldPanel('search_description'),
)


# A couple of abstract classes that contain commonly used fields

class LinkFields(models.Model):
    link_external = models.URLField("External link", blank=True)
    link_page = models.ForeignKey('core.Page', null=True, blank=True, related_name='+')
    link_document = models.ForeignKey('verdantdocs.Document', null=True, blank=True, related_name='+')

    @property
    def link(self):
        if self.link_page:
            return self.link_page.url
        elif self.link_document:
            return self.link_document.url
        else:
            return self.link_external

    panels = [
        FieldPanel('link_external'),
        PageChooserPanel('link_page'),
        DocumentChooserPanel('link_document'),
    ]

    class Meta:
        abstract = True


class ContactFields(models.Model):
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address_1 = models.CharField(max_length=255, blank=True)
    address_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    post_code = models.CharField(max_length=10, blank=True)

    panels = [
        FieldPanel('telephone'),
        FieldPanel('email'),
        FieldPanel('address_1'),
        FieldPanel('address_2'),
        FieldPanel('city'),
        FieldPanel('country'),
        FieldPanel('post_code'),
    ]

    class Meta:
        abstract = True


# Carousel items

class CarouselItem(LinkFields):
    image = models.ForeignKey('verdantimages.Image', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    embed_url = models.URLField("Embed URL", blank=True)
    caption = models.CharField(max_length=255, blank=True)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('embed_url'),
        FieldPanel('caption'),
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]

    class Meta:
        abstract = True


# Related links

class RelatedLink(LinkFields):
    title = models.CharField(max_length=255, help_text="Link title")

    panels = [
        FieldPanel('title'),
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]

    class Meta:
        abstract = True

# Home Page

class HomePageCarouselItem(Orderable, CarouselItem):
    page = ParentalKey('demo.DemoHomePage', related_name='carousel_items')

class HomePageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('demo.DemoHomePage', related_name='related_links')

# TODO: Remove the "Demo" prefix. This was added to avoid a name clash with RCA HomePage
class DemoHomePage(Page):
    body = RichTextField(blank=True)

    indexed_fields = ('body', )
    search_name = "Homepage"

    # TODO: Remove this after prefix is put right
    template = 'demo/home_page.html'

    class Meta:
        #verbose_name = "Homepage"
        verbose_name = "DEMO Homepage"

DemoHomePage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('body', classname="full"),
    InlinePanel(DemoHomePage, 'carousel_items', label="Carousel items"),
    InlinePanel(DemoHomePage, 'related_links', label="Related links"),
]

DemoHomePage.promote_panels = [
    MultiFieldPanel(COMMON_PANELS, "Common page configuration"),
]


# Standard index page

class StandardIndexPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('demo.DemoStandardIndexPage', related_name='related_links')

# TODO: Remove the "Demo" prefix. This was added to avoid a name clash with RCA StandardIndexPage
class DemoStandardIndexPage(Page):
    intro = RichTextField(blank=True)

    indexed_fields = ('intro', )

    search_name = None

    # TODO: Remove this after prefix is put right
    template = 'demo/standard_index_page.html'

    class Meta:
        verbose_name = "DEMO Standard Index Page"

DemoStandardIndexPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel(DemoStandardIndexPage, 'related_links', label="Related links"),
]

DemoStandardIndexPage.promote_panels = [
    MultiFieldPanel(COMMON_PANELS, "Common page configuration"),
]


# Standard page

class StandardPageCarouselItem(Orderable, CarouselItem):
    page = ParentalKey('demo.DemoStandardPage', related_name='carousel_items')

class StandardPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('demo.DemoStandardPage', related_name='related_links')

# TODO: Remove the "Demo" prefix. This was added to avoid a name clash with RCA StandardPage
class DemoStandardPage(Page):
    intro = RichTextField(blank=True)
    body = RichTextField(blank=True)

    indexed_fields = ('intro', 'body', )
    search_name = None

    # TODO: Remove this after prefix is put right
    template = 'demo/standard_page.html'

    class Meta:
        verbose_name = "DEMO Standard Page"

DemoStandardPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel(DemoStandardPage, 'carousel_items', label="Carousel items"),
    FieldPanel('body', classname="full"),
    InlinePanel(DemoStandardPage, 'related_links', label="Related links"),
]

DemoStandardPage.promote_panels = [
    MultiFieldPanel(COMMON_PANELS, "Common page configuration"),
]


# Blog index page

class BlogIndexPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('demo.BlogIndexPage', related_name='related_links')

class BlogIndexPage(Page):
    intro = RichTextField(blank=True)

    indexed_fields = ('intro', )
    search_name = "Blog"

    def serve(self, request):
        # Return list of blog pages that are descentands of this page
        blogs = BlogPage.objects.filter(live=True, path__startswith=self.path)

        #filter by tag
        tag = request.GET.get('tag')
    
        if tag:
             blogs = blogs.filter(tags__name=tag)

        #order by most recent date first
        blogs = blogs.distinct().order_by('-date')

        #filter by page
        page = request.GET.get('page')
        paginator = Paginator(blogs, 10)  # Show 10 blogs per page

        try:
            blogs = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            blogs = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            blogs = paginator.page(paginator.num_pages)
        
        return render(request, self.template, {
            'self': self,
            'blogs': blogs,
        })

    class Meta:
        verbose_name = "DEMO Blog Index Page"

BlogIndexPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel(BlogIndexPage, 'related_links', label="Related links"),
]

BlogIndexPage.promote_panels = [
    MultiFieldPanel(COMMON_PANELS, "Common page configuration"),
]


# Blog page

class BlogPageCarouselItem(Orderable, CarouselItem):
    page = ParentalKey('demo.BlogPage', related_name='carousel_items')

class BlogPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('demo.BlogPage', related_name='related_links')

class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey('demo.BlogPage', related_name='tagged_items')

class BlogPage(Page):
    body = RichTextField()
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    date = models.DateField("Post date")

    indexed_fields = ('body', )
    search_name = "Blog Entry"

    class Meta:
        verbose_name = "DEMO Blog Page"

BlogPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('date'),
    FieldPanel('body', classname="full"),
    InlinePanel(BlogPage, 'carousel_items', label="Carousel items"),
    InlinePanel(BlogPage, 'related_links', label="Related links"),
]

BlogPage.promote_panels = [
    MultiFieldPanel(COMMON_PANELS, "Common page configuration"),
    FieldPanel('tags'),
]


# Person page

class PersonPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('demo.PersonPage', related_name='related_links')

class PersonPage(Page, ContactFields):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    intro = RichTextField(blank=True)
    biography = RichTextField(blank=True)
    image = models.ForeignKey('verdantimages.Image', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    indexed_fields = ('first_name', 'last_name', 'intro', 'biography')
    search_name = "Person"

    class Meta:
        verbose_name = "DEMO Person Page"

PersonPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('first_name'),
    FieldPanel('last_name'),
    FieldPanel('intro', classname="full"),
    FieldPanel('biography', classname="full"),
    ImageChooserPanel('image'),
    MultiFieldPanel(ContactFields.panels, "Contact"),
    InlinePanel(PersonPage, 'related_links', label="Related links"),
]

PersonPage.promote_panels = [
    MultiFieldPanel(COMMON_PANELS, "Common page configuration"),
]


# Contact page

class ContactPage(Page, ContactFields):
    body = RichTextField(blank=True)

    indexed_fields = ('body', )
    search_name = "Contact information"

    class Meta:
        verbose_name = "DEMO Contact Page"

ContactPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('body', classname="full"),
    MultiFieldPanel(ContactFields.panels, "Contact"),
]

ContactPage.promote_panels = [
    MultiFieldPanel(COMMON_PANELS, "Common page configuration"),
]


# Event index page

class EventIndexPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('demo.EventIndexPage', related_name='related_links')

class EventIndexPage(Page):
    intro = RichTextField(blank=True)

    indexed_fields = ('intro', )
    search_name = "Event index"

    @property
    def events(self):
        # Get list of event pages that are descentands of this page
        return EventPage.objects.filter(live=True, path__startswith=self.path)

    class Meta:
        verbose_name = "DEMO Event Index Page"

EventIndexPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('intro', classname="full"),
    InlinePanel(EventIndexPage, 'related_links', label="Related links"),
]

EventIndexPage.promote_panels = [
    MultiFieldPanel(COMMON_PANELS, "Common page configuration"),
]


# Event page

class EventPageCarouselItem(Orderable, CarouselItem):
    page = ParentalKey('demo.EventPage', related_name='carousel_items')

class EventPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('demo.EventPage', related_name='related_links')

class EventPageSpeaker(Orderable, LinkFields):
    page = ParentalKey('demo.EventPage', related_name='speakers')
    first_name = models.CharField("Name", max_length=255, blank=True)
    last_name = models.CharField("Surname", max_length=255, blank=True)
    image = models.ForeignKey('verdantimages.Image', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    @property
    def name_display(self):
        return self.first_name + " " + self.last_name

    panels = [
        FieldPanel('first_name'),
        FieldPanel('last_name'),
        ImageChooserPanel('image'),
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]

class EventPage(Page):
    date_from = models.DateField("Start date")
    date_to = models.DateField("End date", null=True, blank=True, help_text="Not required if event is on a single day")
    time_from = models.TimeField("Start time", null=True, blank=True)
    time_to = models.TimeField("End time", null=True, blank=True)
    audience = models.CharField(max_length=255, choices=EVENT_AUDIENCE_CHOICES)
    location = models.CharField(max_length=255)
    body = RichTextField(blank=True)
    cost = models.CharField(max_length=255)
    signup_link = models.URLField(blank=True)

    indexed_fields = ('get_audience_display', 'location', 'body')
    search_name = "Event"

    class Meta:
        verbose_name = "DEMO Event Page"

EventPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('date_from'),
    FieldPanel('date_to'),
    FieldPanel('time_from'),
    FieldPanel('time_to'),
    FieldPanel('location'),
    FieldPanel('audience'),
    FieldPanel('cost'),
    FieldPanel('signup_link'),
    InlinePanel(EventPage, 'carousel_items', label="Carousel items"),
    FieldPanel('body', classname="full"),
    InlinePanel(EventPage, 'speakers', label="Speakers"),
    InlinePanel(EventPage, 'related_links', label="Related links"),
]

EventPage.promote_panels = [
    MultiFieldPanel(COMMON_PANELS, "Common page configuration"),
]