from django.db import models
from verdantadmin.edit_handlers import FieldPanel, PageChooserPanel


class Redirect(models.Model):
    old_path = models.CharField(max_length=255, unique=True, db_index=True)
    site = models.ForeignKey('core.Site', null=True, blank=True, related_name='redirects', db_index=True, editable=False)
    is_permanent = models.BooleanField("Permanent", default=True)
    redirect_page = models.ForeignKey('core.Page', related_name='+', null=True, blank=True)
    redirect_link = models.URLField(blank=True)

    @property
    def title(self):
        return self.old_path

    @property
    def link(self):
        if self.redirect_page:
            return self.redirect_page.url
        else:
            return self.redirect_link

    def get_is_permanent_display(self):
        if self.is_permanent:
            return "Permanent"
        else:
            return "Temporary"

    @classmethod
    def get_for_site(cls, site=None):
        if site:
            return cls.objects.filter(models.Q(site=site) | models.Q(site=None))
        else:
            return cls.objects.all()

    @staticmethod
    def normalise_path(path):
        # Check that the path has content before normalising
        if path is None or path == '':
            return ''

        # Make sure theres a '/' at the beginning
        if path[0] != '/':
            path = '/' + path

        # Make sure theres not a '/' at the end
        if path[-1] == '/':
            path = path[:-1]

        return path

    def clean(self):
        # Normalise old path
        self.old_path = Redirect.normalise_path(self.old_path)

Redirect.content_panels = [
    FieldPanel('old_path'),
    FieldPanel('is_permanent'),
    PageChooserPanel('redirect_page'),
    FieldPanel('redirect_link'),
]