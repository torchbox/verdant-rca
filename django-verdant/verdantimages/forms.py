from django import forms
from django.forms.models import modelform_factory

from verdantimages.models import get_image_model
from verdantimages.formats import FORMATS


def get_image_form():
    return modelform_factory(get_image_model())

def get_edit_image_form():
    return modelform_factory(get_image_model(), exclude=['file'])


class ImageInsertionForm(forms.Form):
    """
    Form for selecting parameters of the image (e.g. format) prior to insertion
    into a rich text area
    """
    format = forms.ChoiceField(
        choices=[(format.name, format.label) for format in FORMATS],
        widget=forms.RadioSelect
    )
    alt_text = forms.CharField()
