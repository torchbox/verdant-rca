from django import forms
from .fields import CreditCardField, ExpiryDateField, VerificationValueField


class DonationForm(forms.Form):
    card_number = CreditCardField(required=True)
    expiration = ExpiryDateField(required=True)
    cvc = VerificationValueField(required=True)
    is_gift_aid = forms.BooleanField()
    email = forms.EmailField(required=False)
    title           = forms.CharField(required=False, max_length=255)
    first_name      = forms.CharField(required=False, max_length=255)
    last_name       = forms.CharField(required=False, max_length=255)
    address_line_1  = forms.CharField(required=False, max_length=255)
    address_line_2  = forms.CharField(required=False, max_length=255)
    town            = forms.CharField(required=False, max_length=255)
    county          = forms.CharField(required=False, max_length=255)
    postcode        = forms.CharField(required=False, max_length=255)
    country         = forms.CharField(required=False, max_length=255)
    phone           = forms.CharField(required=False, max_length=255)