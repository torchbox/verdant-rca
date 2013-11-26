# -*- coding: utf-8 -*-

from decimal import Decimal

from django.core import validators
from django import forms
from donations.fields import CreditCardField, ExpiryDateField, VerificationValueField, EmptyValueAttrWidget


class DonationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(DonationForm, self).__init__(*args, **kwargs)
        # the EmptyValueAttrWidget makes sure not to render the single use token on the page
        self.fields['stripe_token'].widget = EmptyValueAttrWidget()
        self.fields['name'].widget = forms.HiddenInput()
        self.fields['name'].initial = ""  # name on card is optional and set by javascript

    required_css_class = 'required'

    METADATA_FIELDS = ['title', 'first_name', 'last_name', 'is_gift_aid', 'email', 'phone', 'class_year', 'donation_for', 'affiliation', 'not_included_in_supporters_list']  # 'phone_type'

    UNREADABLE_FIELDS = ['number', 'cvc', 'expiration']

    amounts = forms.ChoiceField(label="Please select one of our suggested donation amounts or specify another amount", widget=forms.RadioSelect(), required=False, initial=50, choices=(
        ("50", "£50"),
        ("100", "£100"),
        ("250", "£250"),
        ("500", "£500"),
        ("1000", "£1000"),
        ("", "Other"),
    ))
    amount = forms.FloatField(label="Other amount", required=False)

    number = CreditCardField(label="Card number", required=False)
    expiration = ExpiryDateField(required=False)
    cvc = VerificationValueField(required=False, help_text="The 3-digit security code printed on the signature strip on the reverse")
    is_gift_aid = forms.BooleanField(label="I would like the royal college of art to claim gift aid on all my qualifying donations from the date of this declaration until I notify the college otherwise. I confirm that I have paid an amount of UK income tax or capital gains tax at least equal to the amount of tax that all the charities or community amateur sports clubs I donate to will reclaim on my donations for the tax year.", required=False)
    email = forms.EmailField(required=True)
    not_included_in_supporters_list = forms.BooleanField(label="Please tick this box if you do not wish to be included in our list of supporters", required=False, help_text="")

    title           = forms.CharField(required=True, max_length=255)
    first_name      = forms.CharField(required=True, max_length=255)
    last_name       = forms.CharField(required=True, max_length=255)
    address_line1   = forms.CharField(label="Address line 1", required=True, max_length=255)
    address_line2   = forms.CharField(label="Address line 2", required=False, max_length=255)
    address_city    = forms.CharField(label="Town", required=True, max_length=255)
    address_state   = forms.CharField(label="County", required=False, max_length=255)
    address_zip     = forms.CharField(label="Postcode", required=True, max_length=255)
    address_country = forms.CharField(label="Country", required=True, max_length=255)
    phone           = forms.CharField(required=True, max_length=255)

    # phone_type = forms.ChoiceField(required=False, choices=(
    #         ("home", "Home"),
    #         ("business", "Business"),
    #         ("mobile", "Mobile"),
    # ))

    affiliation = forms.ChoiceField(label="*Affiliation with the RCA", required=True, choices=(
            ("Alumnus/alumna", "Alumnus/alumna"),
            ("staff", "Staff"),
            ("friend", "Friend"),
            ("parent", "Parent"),
    ))

    donation_for = forms.ChoiceField(label="Please direct my gift towards", required=True, choices=(
            ("scholarships", "Scholarships"),
            ("college_greatest_need", "College’s greatest need"),
    ))
    class_year = forms.CharField(label="Class year", required=False, max_length=255)

    name = forms.CharField(required=False, max_length=255)
    stripe_token = forms.CharField(required=False, max_length=255)

    def clean_amount(self):
        # stripe uses cents for the amount, i.e. $1.23 is represented as 123
        if self.cleaned_data['amount']:
            self.cleaned_data['amount'] = int(Decimal(self.cleaned_data['amount']) * 100)
        else:
            self.cleaned_data['amount'] = int(Decimal(self.cleaned_data['amounts']) * 100)
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

