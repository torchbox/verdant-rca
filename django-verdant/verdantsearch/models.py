from django.db import models
from django.utils import timezone
from core.models import Page
from indexed import Indexed
from searcher import Searcher
import datetime


class SearchTerms(models.Model):
    terms = models.CharField(max_length=255, unique=True)
    past_hits = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        # Normalise terms
        self.terms = self.normalise_terms(self.terms)

        super(SearchTerms, self).save(*args, **kwargs)

    def add_hit(self):
        daily_hits, created = SearchTermsDailyHits.objects.get_or_create(terms=self, date=timezone.now().date())
        daily_hits.hits = models.F('hits') + 1
        daily_hits.save()

    def get_hits_since(self, since_date):
        return self.daily_hits.filter(date__gte=since_date).aggregate(models.Sum('hits'))['hits__sum']

    @property
    def past_month_hits(self):
        today = timezone.now().date()
        return self.get_hits_since(today - datetime.timedelta(days=30))

    @property
    def past_week_hits(self):
        today = timezone.now().date()
        return self.get_hits_since(today - datetime.timedelta(days=7))

    @property
    def today_hits(self):
        today = timezone.now().date()
        return self.get_hits_since(today)

    @property
    def total_hits(self):
        # Get number of hits in daily hits records
        daily_hits_hits = self.daily_hits.aggregate(models.Sum('hits'))['hits__sum']

        # Add to past hits and return
        return daily_hits_hits + self.past_hits

    @classmethod
    def get(cls, terms):
        return cls.objects.get_or_create(terms=cls.normalise_terms(terms))[0]

    @classmethod
    def get_most_popular(cls, date_since=None):
        return cls.objects.all() # TODO: Return search terms in order of popularity

    @staticmethod
    def normalise_terms(terms):
        return terms.lower()


class SearchTermsDailyHits(models.Model):
    terms = models.ForeignKey(SearchTerms, related_name='daily_hits')
    date = models.DateField()
    hits = models.IntegerField(default=0)

    class Meta:
        unique_together = (
            ('terms', 'date'),
        )


class EditorsPick(models.Model):
    terms = models.ForeignKey(SearchTerms, db_index=True, related_name='editors_picks')
    page = models.ForeignKey('core.Page')
    sort_order = models.IntegerField(default=0)
    description = models.TextField()


# Used for tests

class SearchTest(models.Model, Indexed):
    title = models.CharField(max_length=255)
    content = models.TextField()

    indexed_fields = ("title", "content")

    title_search = Searcher(["title"])


class SearchTestChild(SearchTest):
    extra_content = models.TextField()

    indexed_fields = "extra_content"