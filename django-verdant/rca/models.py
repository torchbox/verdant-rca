from django.db import models
from django import forms

from core.models import Page
from verdantadmin.forms import register, AdminHandler


class EditorialPage(Page):
    body = models.TextField()


class NewsIndex(Page):
    subpage_types = ['NewsItem']


class NewsItem(EditorialPage):
    pass


class NewsItemForm(forms.ModelForm):
    class Meta:
        model = NewsItem
        exclude = ['content_type', 'path', 'depth', 'numchild', 'sluug']


class NewsItemAdminHandler(AdminHandler):
    form = NewsItemForm


register(NewsItem, NewsItemAdminHandler)
