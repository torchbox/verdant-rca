from django import forms
from django.forms.models import inlineformset_factory
import models


class SearchTermsForm(forms.ModelForm):
    class Meta:
        model = models.SearchTerms


class EditorsPickForm(forms.ModelForm):
    class Meta:
        model = models.EditorsPick

EditorsPickFormSet = inlineformset_factory(models.SearchTerms, models.EditorsPick, can_order=True, can_delete=True, extra=0)