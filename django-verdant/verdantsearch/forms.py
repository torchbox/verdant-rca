from django import forms
from django.forms.models import inlineformset_factory
import models


class SearchTermsForm(forms.Form):
    terms = forms.CharField(required=True)


class EditorsPickForm(forms.ModelForm):
    sort_order = forms.IntegerField(required=False)

    def __init__(self, *args, **kwargs):
        super(EditorsPickForm, self).__init__(*args, **kwargs)
        self.fields['page'].widget = forms.HiddenInput()

    class Meta:
        model = models.EditorsPick


EditorsPickFormSetBase = inlineformset_factory(models.SearchTerms, models.EditorsPick, form=EditorsPickForm, can_order=True, can_delete=True, extra=0)

class EditorsPickFormSet(EditorsPickFormSetBase):
    def add_fields(self, form, *args, **kwargs):
        super(EditorsPickFormSet, self).add_fields(form, *args, **kwargs)

        # Hide delete and order fields
        form.fields['DELETE'].widget = forms.HiddenInput()
        form.fields['ORDER'].widget = forms.HiddenInput()

        # Remove terms field
        del form.fields['terms']

    def save(self, commit=True):
        super(EditorsPickFormSet, self).save(commit=False)

        # Set sort_order
        for i, form in enumerate(self.ordered_forms):
            form.instance.sort_order = i

        # Save
        if commit:
            super(EditorsPickFormSet, self).save(commit=True)