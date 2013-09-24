from django import forms

from verdantdocs.models import Document


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        widgets = {
            'file': forms.FileInput()
        }
