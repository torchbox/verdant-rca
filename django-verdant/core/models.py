from django.db import models

class Site(models.Model):
	hostname = models.CharField(max_length=255)
	root_page = models.ForeignKey('Page')

class Page(models.Model):
	title = models.CharField(max_length=255)
	slug = models.SlugField()
	parent = models.ForeignKey('self', blank=True, null=True, related_name='subpages')
