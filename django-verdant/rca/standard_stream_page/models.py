from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.wagtailadmin.edit_handlers import FieldPanel, InlinePanel, MultiFieldPanel, PublishingPanel, \
    StreamFieldPanel
from wagtail.wagtailcore.fields import RichTextField, StreamField
from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailsearch import index

from rca.models import SocialFields, SidebarBehaviourFields, RelatedLinkMixin
from .blocks import StandardStreamBlock


class StandardStreamPageRelatedLink(Orderable, RelatedLinkMixin):
    page = ParentalKey('standard_stream_page.StandardStreamPage', related_name='related_links')


class StandardStreamPageTag(TaggedItemBase):
    content_object = ParentalKey('standard_stream_page.StandardStreamPage', related_name='tagged_items')


class StandardStreamPage(Page, SocialFields, SidebarBehaviourFields):
    intro = RichTextField(blank=True)
    strapline = models.CharField(max_length=255, blank=True)
    # TODO: a single download field or part of a streamfield? https://torchbox.codebasehq.com/projects/rca-django-cms-project/tickets/860#update-41868871
    # download = models.ForeignKey('wagtaildocs.Document', null=True, blank=True, related_name='+')

    body = StreamField(StandardStreamBlock())

    twitter_feed = models.CharField(max_length=255, blank=True, help_text="Replace the default Twitter feed by providing an alternative Twitter handle (without the @ symbol)")
    feed_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text="The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio.")

    related_school = models.ForeignKey('taxonomy.School', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    related_programme = models.ForeignKey('taxonomy.Programme', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    related_area = models.ForeignKey('taxonomy.Area', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    tags = ClusterTaggableManager(through=StandardStreamPageTag, blank=True)

    show_on_homepage = models.BooleanField(default=False)
    show_on_school_page = models.BooleanField(default=False)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        # index.SearchField('body'),
    ]

    # StandardStreamPage with a STUDENT_STORY_TAG or ALUMNI_STORY_TAG can be listed on the packery separately.
    # TODO: This can be done more elegantly with proxy models. See related PR here: https://github.com/torchbox/wagtail/pull/1736/files
    # STUDENT_STORY_TAG = 'student-story'
    # ALUMNI_STORY_TAG = 'alumni-story'

    @property
    def search_name(self):
        if self.related_programme:
            return self.related_programme.display_name

        if self.related_school:
            return self.related_school.display_name

        return None

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('strapline', classname="full"),
        FieldPanel('intro', classname="full"),
        StreamFieldPanel('body'),
        InlinePanel('related_links', label="Related links"),
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
            FieldPanel('related_school'),
            FieldPanel('related_programme'),
            FieldPanel('related_area'),
        ], 'Related pages'),
        FieldPanel('tags'),
    ]

    settings_panels = [
        PublishingPanel(),
        MultiFieldPanel([
            FieldPanel('collapse_upcoming_events'),
        ], 'Sidebar behaviour'),
    ]
