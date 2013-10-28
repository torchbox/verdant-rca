from django.db import models

from cluster.fields import ParentalKey
from cluster.models import ClusterableModel


class Band(ClusterableModel):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class BandMember(models.Model):
    band = ParentalKey('Band', related_name='members')
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class Album(models.Model):
    band = ParentalKey('Band', related_name='albums')
    name = models.CharField(max_length=255)
    release_date = models.DateField(null=True, blank=True)
    sort_order = models.IntegerField(null=True, blank=True, editable=False)

    sort_order_field = 'sort_order'

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['sort_order']


class Place(ClusterableModel):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

class Restaurant(Place):
    serves_hot_dogs = models.BooleanField()
