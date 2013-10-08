from django.db import models
from cluster.fields import ParentalKey


class Band(models.Model):
    name = models.CharField(max_length=255)


class BandMember(models.Model):
    band = ParentalKey('Band', related_name='members')
    name = models.CharField(max_length=255)
