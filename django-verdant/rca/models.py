from django.db import models

from core.models import Page
from core.fields import RichTextField

from verdantadmin.forms import register, AdminHandler
from verdantadmin.panels import FieldPanel, InlinePanel, RichTextFieldPanel, PageChooserPanel
from verdantimages.panels import ImageChooserPanel


class RelatedLink(models.Model):
    url = models.URLField()
    link_text = models.CharField(max_length=255)

    # let's allow related links to have their own images. Just for kicks.
    # (actually, it's so that we can check that the widget override for ImageChooserPanel happens
    # within formsets too)
    image = models.ForeignKey('verdantimages.Image', null=True, blank=True, related_name='+')

    class Meta:
        abstract = True


class EditorialPage(Page):
    body = RichTextField()


# == Authors Index ==
class AuthorsIndex(Page):
    subpage_types = ['AuthorPage']


# == Author Page ==
class AuthorPage(EditorialPage):
    mugshot = models.ForeignKey('verdantimages.Image', null=True, blank=True, related_name='+')

class AuthorPageAdmin(AdminHandler):
    model = AuthorPage

    panels = [
        FieldPanel('title'),
        FieldPanel('slug'),
        ImageChooserPanel('mugshot'),
        RichTextFieldPanel('body'),
    ]

register(AuthorPage, AuthorPageAdmin)

# == News Index ==
class NewsIndex(Page):
    subpage_types = ['NewsItem']


# == News Item ==
class NewsItem(EditorialPage):
    author = models.ForeignKey('rca.AuthorPage', null=True, blank=True, related_name='news_items')
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
        PageChooserPanel('author', AuthorPage),
        ImageChooserPanel('lead_image'),
        RichTextFieldPanel('body'),
        InlinePanel(NewsItem, NewsItemRelatedLink, label="Wonderful related links",
            # label is optional - we'll derive one from the related_name of the relation if not specified
            # Could also pass a panels=[...] argument here if we wanted to customise the display of the inline sub-forms
            panels=[FieldPanel('url'), FieldPanel('link_text'), ImageChooserPanel('image')]
        ),
    ]

register(NewsItem, NewsItemAdminHandler)
