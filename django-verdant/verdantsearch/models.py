from indexed import Indexed
from searcher import Searcher
from django.db import models
from core.models import Page


class EditorsPick(models.Model):
    terms = models.CharField(max_length=255, db_index=True)
    page = models.ForeignKey('core.Page')

    def save(self, *args, **kwargs):
        # Normalise terms
        self.terms = self.normalise_terms(self.terms)

        super(EditorsPick, self).save(*args, **kwargs)

    @classmethod
    def search(cls, terms):
        # Normalise terms
        terms = cls.normalise_terms(terms)

        # Return results
        return Page.objects.filter(editorspick__terms=terms)

    @staticmethod
    def normalise_terms(terms):
        return terms.lower()


# Used for tests

class SearchTest(models.Model, Indexed):
    title = models.CharField(max_length=255)
    content = models.TextField()

    indexed_fields = ("title", "content")

    title_search = Searcher(["title"])


class SearchTestChild(SearchTest):
    extra_content = models.TextField()

    indexed_fields = "extra_content"