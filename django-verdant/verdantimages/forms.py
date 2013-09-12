from django.forms import ModelForm

from verdantimages.models import Image


class ImageForm(ModelForm):
    class Meta:
        model = Image
