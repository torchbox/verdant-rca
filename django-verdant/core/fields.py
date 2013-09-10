from django.db import models
from django.forms import Textarea
from south.modelsinspector import add_introspection_rules

class RichTextArea(Textarea):
    def get_panel(self):
        from verdantadmin.panels import RichTextFieldPanel
        return RichTextFieldPanel


class RichTextField(models.TextField):
    def formfield(self, **kwargs):
        defaults = {'widget': RichTextArea}
        defaults.update(kwargs)
        return super(RichTextField, self).formfield(**defaults)

add_introspection_rules([], ["^core\.fields\.RichTextField"])
