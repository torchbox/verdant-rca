from django.db import models
from django.forms.models import inlineformset_factory

from core.models import Page
from verdantadmin.forms import register, AdminHandler
from verdantadmin.panels import FieldPanel, InlinePanel


class RelatedLink(models.Model):
    url = models.URLField()
    link_text = models.CharField(max_length=255)

    class Meta:
        abstract = True


class EditorialPage(Page):
    body = models.TextField()


class NewsIndex(Page):
    subpage_types = ['NewsItem']


class NewsItem(EditorialPage):
    pass


class NewsItemRelatedLink(RelatedLink):
    news_item = models.ForeignKey('NewsItem', related_name='related_links')


class NewsItemAdminHandler(AdminHandler):
    model = NewsItem
    # can pass a custom modelform here:
    # form = NewsItemForm

    panels = [
        FieldPanel('title'),
        FieldPanel('slug'),
        InlinePanel(inlineformset_factory(NewsItem, NewsItemRelatedLink)),
        FieldPanel('body'),
    ]


# register(NewsItem, NewsItemAdminHandler)
