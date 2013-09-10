from django.db import models
from django.forms import Textarea


class RichTextArea(Textarea):
    def get_panel(self):
        from verdantadmin.panels import RichTextFieldPanel
        return RichTextFieldPanel


class RichTextField(models.TextField):
    def formfield(self, **kwargs):
        defaults = {'widget': RichTextArea}
        defaults.update(kwargs)
        return super(RichTextField, self).formfield(**defaults)
