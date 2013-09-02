from django.db import models

from core.models import Page


class EditorialPage(Page):
    body = models.TextField()


class NewsIndex(Page):
    subpage_types = ['NewsItem']


class NewsItem(EditorialPage):
    pass
