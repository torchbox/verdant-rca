from django.db import models

from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase

from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel, InlinePanel, MultiFieldPanel, PublishingPanel
)
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtaildocs.edit_handlers import DocumentChooserPanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailsearch import index
from wagtail.wagtailsnippets.edit_handlers import SnippetChooserPanel

from rca.help_text import help_text
from rca.models import TWITTER_FEED_HELP_TEXT
from rca.utils.models import (CarouselItemFields, RelatedLinkMixin,
                              SidebarBehaviourFields, SocialFields)


class ShortCourseCarouselItem(Orderable, CarouselItemFields):
    page = ParentalKey(
        'shortcourses.ShortCoursePage',
        related_name='shortcourse_carousel_items'
    )


class ShortCourseRelatedLink(Orderable, RelatedLinkMixin):
    page = ParentalKey(
        'shortcourses.ShortCoursePage',
        related_name='shortcourse_related_links'
    )


class ShortCourseQuotation(Orderable):
    page = ParentalKey(
        'shortcourses.ShortCoursePage',
        related_name='shortcourse_quotations'
    )
    quotation = models.TextField(
        help_text=help_text(
            'shortcourses.ShortCoursePageQuotation', 'quotation'
        )
    )
    quotee = models.CharField(
        max_length=255,
        blank=True,
        help_text=help_text('shortcourses.ShortCoursePageQuotation', 'quotee')
    )
    quotee_job_title = models.CharField(
        max_length=255,
        blank=True,
        help_text=help_text(
            'shortcourses.ShortCoursePageQuotation', 'quotee_job_title'
        )
    )

    panels = [
        FieldPanel('quotation'),
        FieldPanel('quotee'),
        FieldPanel('quotee_job_title')
    ]


class ShortCourseRelatedDocument(Orderable):
    page = ParentalKey(
        'shortcourses.ShortCoursePage',
        related_name='shortcourse_documents'
    )
    document = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        blank=True,
        related_name='+',
        help_text=help_text(
            'shortcourses.ShortCoursePageRelatedDocument', 'document'
        )
    )
    document_name = models.CharField(
        max_length=255,
        help_text=help_text(
            'shortcourses.ShortCoursePageRelatedDocument', 'document_name'
        )
    )

    panels = [
        DocumentChooserPanel('document'),
        FieldPanel('document_name')
    ]


class ShortCourseImage(Orderable):
    page = ParentalKey(
        'shortcourses.ShortCoursePage',
        related_name='shortcourse_images'
    )
    image = models.ForeignKey(
        'rca.RcaImage',
        null=True,
        blank=True,
        related_name='+',
        help_text=help_text('shortcourses.ShortCoursePageImage', 'image')
    )

    panels = [
        ImageChooserPanel('image'),
    ]


class ShortCourseAd(Orderable):
    page = ParentalKey(
        'shortcourses.ShortCoursePage',
        related_name='shortcourse_manual_adverts'
    )
    ad = models.ForeignKey(
        'rca.Advert',
        related_name='+',
        help_text=help_text('shortcourses.ShortCoursePageAd', 'ad')
    )

    panels = [
        SnippetChooserPanel('ad'),
    ]


class ShortCourseReusableTextSnippet(Orderable):
    page = ParentalKey(
        'shortcourses.ShortCoursePage',
        related_name='shortcourse_reusable_text_snippets'
    )
    reusable_text_snippet = models.ForeignKey(
        'rca.ReusableTextSnippet',
        related_name='+',
        help_text=help_text(
            'shortcourses.ShortCoursePageReusableTextSnippet',
            'reusable_text_snippet'
        )
    )

    panels = [
        SnippetChooserPanel('reusable_text_snippet'),
    ]


class ShortCourseTag(TaggedItemBase):
    content_object = ParentalKey(
        'shortcourses.ShortCoursePage',
        related_name='tagged_items'
    )


class ShortCoursePageKeyword(TaggedItemBase):
    content_object = ParentalKey(
        'shortcourses.ShortCoursePage', on_delete=models.CASCADE)


class ShortCoursePage(Page, SocialFields, SidebarBehaviourFields):
    parent_page_types = ['rca.StandardIndex']

    intro = RichTextField(
        help_text=help_text('shortcourses.ShortCoursePage', 'intro'),
        blank=True
    )
    body = RichTextField(
        help_text=help_text('shortcourses.ShortCoursePage', 'body')
    )
    strapline = models.CharField(
        max_length=255,
        blank=True,
        help_text=help_text('shortcourses.ShortCoursePage', 'strapline')
    )
    middle_column_body = RichTextField(
        blank=True,
        help_text=help_text(
            'shortcourses.ShortCoursePage', 'middle_column_body')
    )
    show_on_homepage = models.BooleanField(
        default=False,
        help_text=help_text('shortcourses.ShortCoursePage', 'show_on_homepage')
    )
    twitter_feed = models.CharField(
        max_length=255,
        blank=True,
        help_text=help_text(
            'shortcourses.ShortCoursePage',
            'twitter_feed', default=TWITTER_FEED_HELP_TEXT
        )
    )
    related_school = models.ForeignKey(
        'taxonomy.School',
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name='shortcourses',
        help_text=help_text('shortcourses.ShortCoursePage', 'related_school'),
        verbose_name='School'
    )
    related_programme = models.ForeignKey(
        'taxonomy.Programme',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='shortcourses',
        help_text=help_text(
            'shortcourses.ShortCoursePage', 'related_programme')
    )
    related_area = models.ForeignKey(
        'taxonomy.Area',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='shortcourses',
        help_text=help_text('shortcourses.ShortCoursePage', 'related_area')
    )
    feed_image = models.ForeignKey(
        'rca.RcaImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text=help_text(
            'shortcourses.ShortCoursePage',
            'feed_image',
            default="The image displayed in content feeds, such as the news "
                    "carousel. Should be 16:9 ratio."
        )
    )
    tags = ClusterTaggableManager(
        through=ShortCourseTag,
        help_text=help_text('shortcourses.ShortCoursePage', 'tags'),
        blank=True
    )
    show_on_school_page = models.BooleanField(
        default=False,
        help_text=help_text(
            'shortcourses.ShortCoursePage', 'show_on_school_page')
    )
    programme_finder_exclude = models.BooleanField(
        default=False,
        verbose_name='Exclude from programme finder',
        help_text='Tick to exclude this page from the programme finder.'
    )
    programme_finder_keywords = ClusterTaggableManager(
        through=ShortCoursePageKeyword,
        blank=True,
        verbose_name='Keywords',
        help_text='A comma-separated list of keywords.',
        related_name='shortcourse_keywords'
    )
    degree_level = models.ForeignKey(
        'taxonomy.DegreeLevel',
        null=True,
        on_delete=models.SET_NULL,
        related_name='degree_shortcourse_pages'
    )

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

    # ShortCourses with a STUDENT_STORY_TAG or ALUMNI_STORY_TAG can be listed
    # on the homepage packery separately.
    # TODO: This can be done more elegantly with proxy models. See related PR
    # here: https://github.com/torchbox/wagtail/pull/1736/files
    # STUDENT_STORY_TAG = 'student-story'
    # ALUMNI_STORY_TAG = 'alumni-story'

    @property
    def search_name(self):
        if self.related_programme:
            return self.related_programme.display_name

        if self.related_school:
            return self.related_school.display_name

        return None

    @property
    def carousel_items(self):
        return self.shortcourse_carousel_items

    @property
    def related_links(self):
        return self.shortcourse_related_links

    @property
    def reusable_text_snippets(self):
        return self.shortcourse_reusable_text_snippets

    @property
    def documents(self):
        return self.shortcourse_documents

    @property
    def quotations(self):
        return self.shortcourse_quotations

    @property
    def images(self):
        return self.shortcourse_images

    @property
    def manual_adverts(self):
        return self.shortcourse_manual_adverts

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('strapline', classname="full"),
        FieldPanel('intro', classname="full"),
        FieldPanel('body', classname="full"),
        InlinePanel('shortcourse_carousel_items', label="Carousel content"),
        InlinePanel('shortcourse_related_links', label="Related links"),
        FieldPanel('middle_column_body', classname="full"),
        InlinePanel(
            'shortcourse_reusable_text_snippets',
            label="Reusable text snippet"
        ),
        InlinePanel('shortcourse_documents', label="Document"),
        InlinePanel('shortcourse_quotations', label="Quotation"),
        InlinePanel('shortcourse_images', label="Middle column image"),
        InlinePanel('shortcourse_manual_adverts', label="Manual adverts"),
        FieldPanel('twitter_feed'),
    ]

    promote_panels = [
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
            FieldPanel('related_programme'),
            FieldPanel('related_area'),
        ], 'Related pages'),
        # FieldPanel('tags'),
        FieldPanel('related_school'),
        FieldPanel('degree_level'),
        FieldPanel('programme_finder_keywords'),
        FieldPanel('programme_finder_exclude'),
    ]

    settings_panels = [
        PublishingPanel(),
        MultiFieldPanel([
            FieldPanel('collapse_upcoming_events'),
        ], 'Sidebar behaviour'),
    ]
