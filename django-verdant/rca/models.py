from django.db import models

from core.models import Page


class EditorialPage(Page):
    body = models.TextField()

    template = "rca/editorial_page.html"
