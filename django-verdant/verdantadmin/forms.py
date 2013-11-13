from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import MAXIMUM_PASSWORD_LENGTH

class SearchForm(forms.Form):
    q = forms.CharField(label="Search term")


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
        max_length=MAXIMUM_PASSWORD_LENGTH,
        widget=forms.PasswordInput(attrs={'placeholder': "Enter password"}),
    )
