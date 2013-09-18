from django.db import models
from django.shortcuts import render

from core.models import Page
from core.fields import RichTextField

from verdantadmin.forms import register, AdminHandler
from verdantadmin.panels import FieldPanel, InlinePanel, RichTextFieldPanel, PageChooserPanel
from verdantimages.panels import ImageChooserPanel


class RelatedLink(models.Model):
    page = models.ForeignKey('core.Page', related_name='related_links')
    url = models.URLField()
    link_text = models.CharField(max_length=255)

    # let's allow related links to have their own images. Just for kicks.
    # (actually, it's so that we can check that the widget override for ImageChooserPanel happens
    # within formsets too)
    image = models.ForeignKey('verdantimages.Image', null=True, blank=True, related_name='+')


class EditorialPage(Page):
    body = RichTextField()

    # Setting a class as 'abstract' indicates that it's only intended to be a parent
    # type for more specific page types, and shouldn't be used directly;
    # it will thus be excluded from the list of page types a superuser can create.
    #
    # (NB it still gets a database table behind the scenes, so it isn't abstract
    # by Django's own definition)
    is_abstract = True


# == Authors Index ==
class AuthorsIndex(Page):
    subpage_types = ['AuthorPage']


# == Author Page ==
class AuthorPage(EditorialPage):
    mugshot = models.ForeignKey('verdantimages.Image', null=True, blank=True, related_name='+')

    def serve(self, request):
        news_items = self.news_items.order_by('title')

        return render(request, self.template, {
            'self': self,
            'news_items': news_items,
        })

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
        InlinePanel(Page, RelatedLink, label="Wonderful related links",
            # label is optional - we'll derive one from the related_name of the relation if not specified
            # Could also pass a panels=[...] argument here if we wanted to customise the display of the inline sub-forms
            panels=[FieldPanel('url'), FieldPanel('link_text'), ImageChooserPanel('image')]
        ),
    ]

register(NewsItem, NewsItemAdminHandler)
