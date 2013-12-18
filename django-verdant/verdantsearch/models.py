from indexed import Indexed
from searcher import Searcher
from django.db import models
from core.models import Page


class SearchTerms(models.Model):
    terms = models.CharField(max_length=255, unique=True)
    picks = models.ManyToManyField('core.Page', null=True, blank=True)

    def save(self, *args, **kwargs):
        # Normalise terms
        self.terms = self.normalise_terms(self.terms)

        super(SearchTerms, self).save(*args, **kwargs)

    @classmethod
    def get_picks_for_terms(cls, terms):
        return cls.objects.get(terms=cls.normalise_terms(terms)).picks.all()

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