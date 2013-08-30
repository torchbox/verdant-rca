from django.db import models
from django.http import HttpResponse, Http404


class SiteManager(models.Manager):
    def get_by_natural_key(self, hostname):
        return self.get(hostname=hostname)


class Site(models.Model):
    hostname = models.CharField(max_length=255, unique=True)
    root_page = models.ForeignKey('Page')

    def natural_key(self):
        return (self.hostname,)

    def __unicode__(self):
        if self.hostname == '*':
            return "[Default site]"
        else:
            return self.hostname


class Page(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    parent = models.ForeignKey('self', blank=True, null=True, related_name='subpages')

    def __unicode__(self):
        return self.title

    def route(self, request, path_components):
        if path_components:
            # request is for a child of this page
            child_slug = path_components[0]
            remaining_components = path_components[1:]

            try:
                subpage = self.subpages.get(slug=child_slug)
            except Page.DoesNotExist:
                raise Http404

            return subpage.route(request, remaining_components)

        else:
            # request is for this very page
            return self.serve(request)

    def serve(self, request):
        return HttpResponse("<h1>%s</h1>" % self.title)
