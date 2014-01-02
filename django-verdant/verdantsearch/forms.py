from django import forms
from django.forms.models import inlineformset_factory
import models


class QueryForm(forms.Form):
    query_string = forms.CharField(required=True)


class EditorsPickForm(forms.ModelForm):
    sort_order = forms.IntegerField(required=False)

    def __init__(self, *args, **kwargs):
        super(EditorsPickForm, self).__init__(*args, **kwargs)
        self.fields['page'].widget = forms.HiddenInput()

    class Meta:
        model = models.EditorsPick

        widgets = {
            'description': forms.Textarea(attrs=dict(rows=3)),
        }


EditorsPickFormSetBase = inlineformset_factory(models.Query, models.EditorsPick, form=EditorsPickForm, can_order=True, can_delete=True, extra=0)

class EditorsPickFormSet(EditorsPickFormSetBase):
    def add_fields(self, form, *args, **kwargs):
        super(EditorsPickFormSet, self).add_fields(form, *args, **kwargs)

        # Hide delete and order fields
        form.fields['DELETE'].widget = forms.HiddenInput()
        form.fields['ORDER'].widget = forms.HiddenInput()

        # Remove query field
        del form.fields['query']

    def save(self, *args, **kwargs):
        # Set sort_order
        for i, form in enumerate(self.ordered_forms):
            form.instance.sort_order = i

        super(EditorsPickFormSet, self).save(*args, **kwargs)