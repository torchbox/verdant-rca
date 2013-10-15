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
