# -*- coding: utf-8 -*-

from decimal import Decimal

from django.core import validators
from django import forms
from donations.fields import CreditCardField, ExpiryDateField, VerificationValueField, EmptyValueAttrWidget


SINGLE = 's'
MONTHLY = 'm'
ANNUAL = 'a'

SUBSCRIPTION_CHOICES = (
    (SINGLE, 'Single'),
    (MONTHLY, 'Monthly'),
    (ANNUAL, 'Annual'),
)


class DonationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        show_subscription = kwargs.pop('show_subscription', False)
        super(DonationForm, self).__init__(*args, **kwargs)
        # the EmptyValueAttrWidget makes sure not to render the single use token on the page
        self.fields['stripe_token'].widget = EmptyValueAttrWidget()
        self.fields['name'].widget = forms.HiddenInput()
        self.fields['name'].initial = ""  # name on card is optional and set by javascript
        if not show_subscription:
            del self.fields['subscription']

    required_css_class = 'required'

    METADATA_FIELDS = ['title', 'first_name', 'last_name', 'email', 'phone', 'class_year', 'donation_for', 'affiliation', 'not_included_in_supporters_list']  # 'phone_type'

    UNREADABLE_FIELDS = ['number', 'cvc', 'expiration']

    amounts = forms.ChoiceField(label="Please select one of our suggested donation amounts or specify another amount", widget=forms.RadioSelect(), required=False, initial=50, choices=(
        ("50", "$50"),
        ("100", "$100"),
        ("250", "$250"),
        ("500", "$500"),
        ("1000", "$1000"),
        ("", "Other"),
    ))
    amount = forms.FloatField(label="Other amount", required=False)

    number = CreditCardField(label="Card number", required=False)
    expiration = ExpiryDateField(required=False)
    cvc = VerificationValueField(required=False, help_text="The 3-digit security code printed on the signature strip on the reverse")
    email = forms.EmailField(required=True)
    not_included_in_supporters_list = forms.BooleanField(label="Please tick this box if you do not wish to be included in our list of supporters", required=False, help_text="")

    subscription = forms.ChoiceField(choices=SUBSCRIPTION_CHOICES, label="Please make my payment")

    title           = forms.CharField(required=True, max_length=255)
    first_name      = forms.CharField(required=True, max_length=255)
    last_name       = forms.CharField(required=True, max_length=255)
    address_line1   = forms.CharField(label="Address line 1", required=True, max_length=255)
    address_line2   = forms.CharField(label="Address line 2", required=False, max_length=255)
    address_city    = forms.CharField(label="Town", required=True, max_length=255)
    address_state   = forms.CharField(label="State / Province", required=False, max_length=255)
    address_zip     = forms.CharField(label="ZIP / Postal code", required=True, max_length=255)
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

    class_year = forms.CharField(label="Class year", required=False, max_length=255)

    donation_for = forms.ChoiceField(label="Please direct my gift towards", required=True, choices=(
            # ("scholarships", "Scholarships"),
            # ("storm_thorgerson_scholarship", "Storm Thorgerson Scholarship"),
            # ("wendy_dagworthy_scholarship_fund", "Wendy Dagworthy Scholarship Fund"),
            # ("in_memory_of_dorothy_kemp", "In memory of Dorothy Kemp"),
            # ("college_greatest_need", "College’s greatest need"),
            # ("rca_fund", "RCA Fund"),
            ("gen_rca", "GenerationRCA"),
    ), initial="gen_rca")

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
