from django.db import models

from core.models import Page
from core.fields import RichTextField

from verdantadmin.forms import register, AdminHandler
from verdantadmin.panels import FieldPanel, InlinePanel, RichTextFieldPanel
from verdantimages.panels import ImageChooserPanel


class RelatedLink(models.Model):
    url = models.URLField()
    link_text = models.CharField(max_length=255)

    class Meta:
        abstract = True


class EditorialPage(Page):
    body = RichTextField()


class NewsIndex(Page):
    subpage_types = ['NewsItem']


class NewsItem(EditorialPage):
    lead_image = models.ForeignKey('verdantimages.Image', null=True, blank=True, related_name='+')


class NewsItemRelatedLink(RelatedLink):
    news_item = models.ForeignKey('NewsItem', related_name='related_links')


class NewsItemAdminHandler(AdminHandler):
    model = NewsItem
    # can pass a custom modelform here:
    # form = NewsItemForm

    panels = [
        FieldPanel('title'),
        FieldPanel('slug'),
        ImageChooserPanel('lead_image'),
        RichTextFieldPanel('body'),
        InlinePanel(NewsItem, NewsItemRelatedLink, label="Wonderful related links"),
            # label is optional - we'll derive one from the related_name of the relation if not specified
            # Could also pass a panels=[...] argument here if we wanted to customise the display of the inline sub-forms
    ]


register(NewsItem, NewsItemAdminHandler)
