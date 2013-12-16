from django.db import models


EMBED_TYPES = (
    ('video', 'Video'),
    ('photo', 'Photo'),
    ('link', 'Link'),
    ('rich', 'Rich'),
)


class SavedEmbed(models.Model):
    url = models.URLField()
    maxwidth = models.SmallIntegerField(null=True, blank=True)
    type = models.CharField(max_length=10, choices=EMBED_TYPES)
    html = models.TextField(blank=True)
    title = models.TextField(blank=True)
    thumbnail_url = models.URLField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('url', 'maxwidth')

    def __unicode__(self):
        return self.url