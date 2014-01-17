from django import forms

from verdantdocs.models import Document


class DocumentForm(forms.ModelForm):
    required_css_class = "required"

    class Meta:
        model = Document
        widgets = {
            'file': forms.FileInput()
        }
