from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

from taggit.managers import TaggableManager
from taggit.models import Tag

class Document(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents')

    tags = TaggableManager(help_text=None)

    def __unicode__(self):
        return self.title

# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(pre_delete, sender=Document)
def image_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)
