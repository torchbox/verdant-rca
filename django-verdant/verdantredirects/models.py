from django.db import models


REDIRECT_TYPE_CHOICES = (
    (False, "Temporary"),
    (True, "Permanent"),
)


class Redirect(models.Model):
    old_path = models.CharField(max_length=255, unique=True, db_index=True)
    site = models.ForeignKey('core.Site', null=True, blank=True, related_name='redirects', db_index=True, editable=False)
    is_permanent = models.BooleanField("Type", default=True, choices=REDIRECT_TYPE_CHOICES)
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

    @classmethod
    def get_for_site(cls, site=None):
        if site:
            return cls.objects.filter(models.Q(site=site) | models.Q(site=None))
        else:
            return cls.objects.all()

    @staticmethod
    def normalise_path(path):
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