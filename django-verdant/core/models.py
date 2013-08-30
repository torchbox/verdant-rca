from django.db import models


class SiteManager(models.Manager):
    def get_by_natural_key(self, hostname):
        return self.get(hostname=hostname)


class Site(models.Model):
    hostname = models.CharField(max_length=255, unique=True)
    root_page = models.ForeignKey('Page')

    def natural_key(self):
        return (self.name,)


class Page(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    parent = models.ForeignKey('self', blank=True, null=True, related_name='subpages')
