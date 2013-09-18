from django import forms

from verdantimages.models import Image
from verdantimages.formats import FORMATS


class ImageForm(forms.ModelForm):
    class Meta:
        model = Image


class EditImageForm(forms.ModelForm):
    class Meta:
        model = Image
        exclude = ['file']


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
