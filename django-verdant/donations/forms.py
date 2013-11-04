from decimal import Decimal

from django.core import validators
from django import forms
from .fields import CreditCardField, ExpiryDateField, VerificationValueField, EmptyValueAttrWidget


class DonationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(DonationForm, self).__init__(*args, **kwargs)
        # the EmptyValueAttrWidget makes sure not to render the single use token on the page
        self.fields['stripe_token'].widget = EmptyValueAttrWidget()
        self.fields['name'].widget = forms.HiddenInput()
        self.fields['name'].initial = ""  # name on card is optional and set by javascript

    METADATA_FIELDS = ['title', 'first_name', 'last_name', 'is_gift_aid', 'email', 'phone']
    UNREADABLE_FIELDS = ['number', 'cvc', 'expiration']

    amount = forms.FloatField(required=True)
    number = CreditCardField(label="Card number", required=False)
    expiration = ExpiryDateField(required=False)
    cvc = VerificationValueField(required=False)
    is_gift_aid = forms.BooleanField(required=False)
    email = forms.EmailField(required=False)
    title           = forms.CharField(required=False, max_length=255)
    first_name      = forms.CharField(required=False, max_length=255)
    last_name       = forms.CharField(required=False, max_length=255)
    address_line1   = forms.CharField(label="Address line 1", required=False, max_length=255)
    address_line2   = forms.CharField(label="Address line 2", required=False, max_length=255)
    address_city    = forms.CharField(label="Town", required=False, max_length=255)
    address_state   = forms.CharField(label="County", required=False, max_length=255)
    address_zip     = forms.CharField(label="Postcode", required=False, max_length=255)
    address_country = forms.CharField(label="Country", required=False, max_length=255)
    phone           = forms.CharField(required=False, max_length=255)

    name = forms.CharField(required=False, max_length=255)
    stripe_token = forms.CharField(required=False, max_length=255)

    def clean_amount(self):
        # stripe uses cents for the amount
        # i.e. $1.23 is represented as 123
        self.cleaned_data['amount'] = int(Decimal(self.cleaned_data['amount']) * 100)
        return self.cleaned_data['amount']

    def clean(self):
        # the matadat field allows as to store extra information for each payment
        self.cleaned_data['metadata'] = {}
        for f in self.METADATA_FIELDS:
            if f in self.cleaned_data:
                self.cleaned_data['metadata'][f] = self.cleaned_data[f]

        # make sure we're not storing any credit card data on the server
        for f in self.UNREADABLE_FIELDS:
            if f in self.cleaned_data:
                del self.cleaned_data[f]

        return self.cleaned_data

