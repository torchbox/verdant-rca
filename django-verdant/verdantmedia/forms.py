from django import forms


class MediaForm(forms.Form):
	url = forms.CharField(label="URL")