from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.core.urlresolvers import reverse

import os.path

from taggit.managers import TaggableManager

from verdantadmin.taggable import TagSearchable


class Document(models.Model, TagSearchable):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents')
    created_at = models.DateTimeField(auto_now_add=True)

    tags = TaggableManager(help_text=None, blank=True)

    def __unicode__(self):
        return self.title

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def url(self):
        return reverse('verdantdocs_serve', args=[self.id, self.filename])

# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(pre_delete, sender=Document)
def image_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)
