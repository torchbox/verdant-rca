from django import forms
from django.contrib.auth.forms import AuthenticationForm

class SearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        placeholder_suffix = kwargs.pop('placeholder_suffix', "")
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['q'].widget.attrs = {'placeholder': 'Search ' + placeholder_suffix}
    
    q = forms.CharField(label="Search term", widget=forms.TextInput())

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


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={'placeholder': "Enter your username"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': "Enter password"}),
    )
