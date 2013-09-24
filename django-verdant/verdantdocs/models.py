from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.core.urlresolvers import reverse

import os.path

from taggit.managers import TaggableManager
from taggit.models import Tag

class Document(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents')

    tags = TaggableManager(help_text=None)

    def __unicode__(self):
        return self.title

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def url(self):
        return reverse('verdantdocs_serve', args=[self.id, self.filename])

    @staticmethod
    def search(q):
        # TODO: DRY this method with the one on verdantimages.models.AbstractImage
        # TODO: speed up this search - currently istartswith is doing sequential scan
        strings = q.split()
        # match according to tags first
        tags = Tag.objects.none()
        for string in strings:
            tags = tags | Tag.objects.filter(name__startswith=string)
        # NB the following line will select documents if any tags match, not just if all do
        tag_matches = Document.objects.filter(tags__in = tags).distinct()
        # now match according to titles
        title_matches = Document.objects.none()
        documents = Document.objects.all()
        for term in strings:
            title_matches = title_matches | documents.filter(title__istartswith=term).distinct()
        documents = tag_matches | title_matches
        return documents

# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(pre_delete, sender=Document)
def image_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)
