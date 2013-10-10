from django import forms

class SearchForm(forms.Form):
    q = forms.CharField(label = "Search term")


class ExternalLinkChooserForm(forms.Form):
    url = forms.URLField(required=True)

class ExternalLinkChooserWithLinkTextForm(forms.Form):
    url = forms.URLField(required=True)
    link_text = forms.CharField(required=True)

class EmailLinkChooserForm(forms.Form):
    email_address = forms.EmailField(required=True)

class EmailLinkChooserWithLinkTextForm(forms.Form):
    email_address = forms.EmailField(required=True)
    link_text = forms.CharField(required=False)
