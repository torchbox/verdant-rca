from django.db import models
from django.forms import Textarea
from south.modelsinspector import add_introspection_rules

from core.rich_text import to_db_html, to_editor_html

class RichTextArea(Textarea):
    def get_panel(self):
        from verdantadmin.panels import RichTextFieldPanel
        return RichTextFieldPanel

    def render(self, name, value, attrs=None):
        translated_value = to_editor_html(value)
        return super(RichTextArea, self).render(name, translated_value, attrs)

    def value_from_datadict(self, data, files, name):
        original_value = super(RichTextArea, self).value_from_datadict(data, files, name)
        return to_db_html(original_value)


class RichTextField(models.TextField):
    def formfield(self, **kwargs):
        defaults = {'widget': RichTextArea}
        defaults.update(kwargs)
        return super(RichTextField, self).formfield(**defaults)

add_introspection_rules([], ["^core\.fields\.RichTextField"])
