from django import forms
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from verdantimages.models import get_image_model


def validate_url(url):
    validator = URLValidator()
    try:
        validator(url)
    except ValidationError:
        raise ValidationError('Please enter a valid URL')


def validate_image_exists(image_id):
    if image_id is None:
        return

    model = get_image_model()
    try:
        img = model.objects.get(pk=image_id)
    except model.DoesNotExist:
        raise ValidationError('This image doesn\'t exist')


class MediaForm(forms.Form):
    url = forms.CharField(label='URL', validators=[validate_url])
    poster_image_id = forms.IntegerField(label='Poster Image', required=False, validators=[validate_image_exists])