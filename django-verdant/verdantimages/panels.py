from django import forms
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from verdantadmin.panels import BaseFieldPanel


class BaseImageChooserPanel(BaseFieldPanel):
    template = "verdantimages/panels/image_chooser_panel.html"

    @classmethod
    def widgets(cls):
        return {
            cls.field_name: forms.HiddenInput
        }

    def render(self):
        return mark_safe(render_to_string(self.template, {
            'field': self.form[self.field_name],
            'image': getattr(self.model_instance, self.field_name)
        }))

    def render_js(self):
        return "createImageChooser(fixPrefix('%s'));" % self.form[self.field_name].id_for_label

def ImageChooserPanel(field_name):
    return type('_ImageChooserPanel', (BaseImageChooserPanel,), {'field_name': field_name})
