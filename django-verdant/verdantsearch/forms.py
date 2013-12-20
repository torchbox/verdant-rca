from django import forms
from django.forms.models import inlineformset_factory
import models


class SearchTermsForm(forms.ModelForm):
    class Meta:
        model = models.SearchTerms


class EditorsPickForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EditorsPickForm, self).__init__(*args, **kwargs)
        self.fields['page'].widget = forms.HiddenInput()

    class Meta:
        model = models.EditorsPick


EditorsPickFormSet = inlineformset_factory(models.SearchTerms, models.EditorsPick, form=EditorsPickForm, can_order=True, can_delete=True, extra=1)