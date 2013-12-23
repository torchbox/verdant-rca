from django.db import models
from django.utils import timezone
from core.models import Page
from indexed import Indexed
from searcher import Searcher
import datetime
import string


class SearchTerms(models.Model):
    terms = models.CharField(max_length=255, unique=True)

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

    @classmethod
    def garbage_collect(cls):
        """
        Deletes all SearchTerms records that have no daily hits or editors picks
        """
        cls.objects.filter(daily_hits__isnull=True, editors_picks__isnull=True).delete()

    @classmethod
    def get(cls, terms):
        return cls.objects.get_or_create(terms=cls.normalise_terms(terms))[0]

    @classmethod
    def get_most_popular(cls, date_since=None):
        return cls.objects.filter(daily_hits__isnull=False).annotate(hits=models.Sum('daily_hits__hits')).distinct().order_by('-hits')

    @staticmethod
    def normalise_terms(terms):
        # Convert terms to lowercase
        terms = terms.lower()

        # Strip punctuation characters
        terms = ''.join([c for c in terms if c not in string.punctuation])

        # Remove double spaces
        ' '.join(terms.split())

        return terms


class SearchTermsDailyHits(models.Model):
    terms = models.ForeignKey(SearchTerms, db_index=True, related_name='daily_hits')
    date = models.DateField()
    hits = models.IntegerField(default=0)

    @classmethod
    def garbage_collect(cls, max_age=30):
        """
        Deletes all SearchTermsDailyHits records that are older than max_age days
        """
        min_date = timezone.now().date() - datetime.timedelta(days=7)

        cls.objects.filter(date__lt=min_date).delete()

    class Meta:
        unique_together = (
            ('terms', 'date'),
        )


class EditorsPick(models.Model):
    terms = models.ForeignKey(SearchTerms, db_index=True, related_name='editors_picks')
    page = models.ForeignKey('core.Page')
    sort_order = models.IntegerField(null=True, blank=True, editable=False)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ('sort_order', )


# Used for tests

class SearchTest(models.Model, Indexed):
    title = models.CharField(max_length=255)
    content = models.TextField()

    indexed_fields = ("title", "content")

    title_search = Searcher(["title"])


class SearchTestChild(SearchTest):
    extra_content = models.TextField()

    indexed_fields = "extra_content"