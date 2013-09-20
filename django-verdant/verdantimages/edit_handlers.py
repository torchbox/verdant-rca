from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.forms import HiddenInput

from verdantadmin.edit_handlers import BaseFieldPanel

class BaseImageChooserPanel(BaseFieldPanel):
    field_template = "verdantimages/edit_handlers/image_chooser_panel.html"

    @classmethod
    def widget_overrides(cls):
        return {cls.field_name: HiddenInput}

    def render_as_field(self, show_help_text=True):
        return mark_safe(render_to_string(self.field_template, {
            'field': self.bound_field,
            'image': getattr(self.instance, self.field_name),
            'show_help_text': show_help_text,
        }))

    def render_js(self):
        return mark_safe("createImageChooser(fixPrefix('%s'));" % self.bound_field.id_for_label)

def ImageChooserPanel(field_name):
    return type('_ImageChooserPanel', (BaseImageChooserPanel,), {
        'field_name': field_name,
    })
