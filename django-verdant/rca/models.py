from django.db import models
from django import forms
from django.forms.models import inlineformset_factory

from core.models import Page
from verdantadmin.forms import register, AdminHandler


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


class NewsItemForm(forms.ModelForm):
    class Meta:
        model = NewsItem
        exclude = ['content_type', 'path', 'depth', 'numchild', 'sluug']


class NewsItemAdminHandler(AdminHandler):
    form = NewsItemForm
    inlines = [inlineformset_factory(NewsItem, NewsItemRelatedLink)]


register(NewsItem, NewsItemAdminHandler)
