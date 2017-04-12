from django.db import models
from wagtail.wagtailadmin.edit_handlers import PageChooserPanel, FieldPanel

from wagtail.wagtailcore.models import Page
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel

from rca.help_text import help_text


class RelatedLinkMixin(models.Model):
    """Related link item abstract class - all related links basically require the same fields"""

    link = models.ForeignKey(Page, null=True, blank=True, related_name='+', help_text=help_text('utils.RelatedLinkMixin', 'link'))
    link_external = models.URLField("External link", blank=True, help_text=help_text('utils.RelatedLinkMixin', 'link_external'))
    link_text = models.CharField(max_length=255, blank=True, help_text=help_text('utils.RelatedLinkMixin', 'link_text', default="Link title (or leave blank to use page title"))

    api_fields = [
        'get_link',
        'get_link_text',
    ]

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


class SidebarBehaviourFields(models.Model):
    """Fields that configure how the sidebar of a given page should be treated"""

    collapse_upcoming_events = models.BooleanField(default=False, help_text=help_text('utils.SidebarBehaviourFields',
                                                                                      'collapse_upcoming_events'))

    class Meta:
        abstract = True


class SocialFields(models.Model):
    """Generic social fields abstract class to add social image/text to any new content type easily."""

    social_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
                                     help_text=help_text('utils.SocialFields', 'social_image'))
    social_text = models.CharField(max_length=255, blank=True, help_text=help_text('utils.SocialFields', 'social_text'))

    class Meta:
        abstract = True


class OptionalBlockFields(models.Model):
    """Generic fields to opt out of events and twitter blocks"""
    exclude_twitter_block = models.BooleanField(default=False, help_text=help_text('utils.OptionalBlockFields', 'exclude_twitter_block'))
    exclude_events_sidebar = models.BooleanField(default=False, help_text=help_text('utils.OptionalBlockFields', 'exclude_events_sidebar'))
    exclude_global_adverts = models.BooleanField(default=False, help_text=help_text('utils.OptionalBlockFields', 'exclude_global_adverts'))

    class Meta:
        abstract = True


class CarouselItemFields(models.Model):
    """Carousel item abstract class - all carousels basically require the same fields"""

    image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('utils.CarouselItemFields', 'image'))
    overlay_text = models.CharField(max_length=255, blank=True, help_text=help_text('utils.CarouselItemFields', 'overlay_text'))
    link = models.URLField("External link", blank=True, help_text=help_text('utils.CarouselItemFields', 'link'))
    link_page = models.ForeignKey(Page, on_delete=models.SET_NULL, related_name='+', null=True, blank=True, help_text=help_text('utils.CarouselItemFields', 'link_page'))
    embedly_url = models.URLField('Vimeo URL', blank=True, help_text=help_text('utils.CarouselItemFields', 'embedly_url'))
    poster_image = models.ForeignKey('rca.RcaImage', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', help_text=help_text('utils.CarouselItemFields', 'poster_image'))

    api_fields = [
        'image',
        'overlay_text',
        'poster_image',
        'embedly_url',
        'get_link',
    ]

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
