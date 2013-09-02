from django.db import models
from django.forms import ModelForm
from django.http import Http404
from django.shortcuts import render

from django.contrib.contenttypes.models import ContentType

from core.util import camelcase_to_underscore


class SiteManager(models.Manager):
    def get_by_natural_key(self, hostname):
        return self.get(hostname=hostname)


class Site(models.Model):
    hostname = models.CharField(max_length=255, unique=True, db_index=True)
    root_page = models.ForeignKey('Page')

    def natural_key(self):
        return (self.hostname,)

    def __unicode__(self):
        if self.hostname == '*':
            return "[Default site]"
        else:
            return self.hostname


class PageBase(models.base.ModelBase):
    """Metaclass for Page"""
    def __init__(cls, name, bases, dct):
        super(PageBase, cls).__init__(name, bases, dct)
        if 'template' not in dct:
            # Define a default template path derived from the app name and model name
            cls.template = "%s/%s.html" % (cls._meta.app_label, camelcase_to_underscore(name))
        if 'edit_form' not in dct:
            # define a ModelForm for this page class
            class PageForm(ModelForm):
                class Meta:
                    model = cls

            cls.edit_form = PageForm


class Page(models.Model):
    __metaclass__ = PageBase

    title = models.CharField(max_length=255)
    slug = models.SlugField()
    parent = models.ForeignKey('self', blank=True, null=True, related_name='subpages')
    content_type = models.ForeignKey('contenttypes.ContentType', related_name='pages')

    def __init__(self, *args, **kwargs):
        super(Page, self).__init__(*args, **kwargs)
        if not self.content_type_id:
            # set content type to correctly represent the model class that this was
            # created as
            self.content_type = ContentType.objects.get_for_model(self)

    def __unicode__(self):
        return self.title

    @property
    def specific(self):
        """
            Return this page in its most specific subclassed form.
        """
        # the ContentType.objects manager keeps a cache, so this should potentially
        # avoid a database lookup over doing self.content_type. I think.
        content_type = ContentType.objects.get_for_id(self.content_type_id)
        return content_type.get_object_for_this_type(id=self.id)

    def route(self, request, path_components):
        if path_components:
            # request is for a child of this page
            child_slug = path_components[0]
            remaining_components = path_components[1:]

            try:
                subpage = self.subpages.get(slug=child_slug)
            except Page.DoesNotExist:
                raise Http404

            return subpage.specific.route(request, remaining_components)

        else:
            # request is for this very page
            return self.serve(request)

    def serve(self, request):
        return render(request, self.template, {
            'self': self
        })

    class Meta:
        unique_together = ("parent", "slug")
        index_together = [
            ["parent", "slug"],
        ]
