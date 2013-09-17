from django import forms

from verdantimages.models import Image


class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
