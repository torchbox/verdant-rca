from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

class Image(models.Model):
    title = models.CharField(max_length=255)
    image_file = models.ImageField(upload_to='original_images', width_field='width', height_field='height')
    width = models.IntegerField(editable=False)
    height = models.IntegerField(editable=False)

    def __unicode__(self):
        return self.title

# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(pre_delete, sender=Image)
def mymodel_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.image_file.delete(False)
