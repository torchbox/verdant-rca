from django.db import models
from django import forms

from core.models import Page
from verdantadmin.forms import register


class EditorialPage(Page):
    body = models.TextField()


class NewsIndex(Page):
    subpage_types = ['NewsItem']


class NewsItem(EditorialPage):
    pass


class NewsItemForm(forms.ModelForm):
    class Meta:
        model = NewsItem
        fields = ['title', 'body']

register(NewsItem, NewsItemForm)
