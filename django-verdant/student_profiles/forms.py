from itertools import chain

from django import forms
from django.forms.formsets import formset_factory, BaseFormSet

from rca.help_text import help_text

################################################################################
## internal classes

class ReadonlyForm(forms.Form):
    """Form that allows read-only fields.
    
    To make a field readonly, simply set the property `.readonly = True` on the
    field. The initial value of the field is copied into `cleaned_data`.
    """

    def __init__(self, *args, **kwargs):
        super(ReadonlyForm, self).__init__(*args, **kwargs)
        
        for field in self.fields:
            ffield = self[field].field
            if getattr(ffield, 'readonly', False):
                ffield.required = False

    def clean(self):
        cleaned_data = super(ReadonlyForm, self).clean()

        for field in self.fields:
            ffield = self[field].field
            if getattr(ffield, 'readonly', False):
                cleaned_data[field] = self.initial.get(field)
                self.data[field] = self.initial.get(field)

        return cleaned_data


class RequiredFormSet(BaseFormSet):
    def clean(self):
        """Checks that at least one value is present."""
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return
        if not any(chain(*[form.cleaned_data.values() for form in self.forms])):
            raise forms.ValidationError("At least one value must be present.")


class PhoneNumberField(forms.RegexField):
    """CharField that loosely validates phone numbers.
    
    Phone numbers start with + or 0 and continue with digits, spaces and dashes.
    That's all.
    """

    type = 'phonenumber'

    default_error_messages = {
        'invalid': 'Please enter a valid telephone number. Phone numbers can only contain digits, spaces, "+" and dashes.',
    }

    def __init__(self, *args, **kwargs):
        super(PhoneNumberField, self).__init__(
            r'^[+0][\d -]+$',
            *args, **kwargs)
            
    def clean(self, value):
            if value:
                value = value.strip()
            return super(PhoneNumberField, self).clean(value)  

class BooleanField(forms.BooleanField):
    
    type = 'boolean'  # to make it easier in the template to distinguish what this is!


class RichTextField(forms.CharField):
    # TODO: make this actually render as a rich text!
    
    type = 'richtext'


################################################################################
## Basic Profile

class ProfileBasicForm(ReadonlyForm):
    
    first_name = forms.CharField(
        max_length=255, help_text=help_text('rca.NewStudentPage', 'first_name')
    )
    last_name = forms.CharField(
        max_length=255, help_text=help_text('rca.NewStudentPage', 'last_name')
    )
    last_name.readonly = True
    
    profile_image = forms.ImageField(
        required=False,
        help_text=help_text('rca.NewStudentPage', 'profile_image', default="Self-portrait image, 500x500px"),
    )
    # saves as: models.ForeignKey('rca.RcaImage')
    
    statement = RichTextField(
        required=False,
        help_text=help_text('rca.NewStudentPage', 'statement'),
    )
    
    # remove this later!
    in_show = BooleanField(initial=True)
    in_show.readonly = True
    
    # formsets for:
    # email
    # phone
    # website

class EmailForm(forms.Form):
    email = forms.EmailField(
        required=False,    # because we'll only save those that are there anyway
        #saves NewStudentPageContactsEmail
    )
EmailFormset = formset_factory(EmailForm, extra=1, formset=RequiredFormSet)
    
class PhoneForm(forms.Form):
    phone = PhoneNumberField(
        required=False,    # because we'll only save those that are there anyway
        #saves NewStudentPageContactsPhone
    )
PhoneFormset = formset_factory(PhoneForm, extra=1, formset=RequiredFormSet)

class WebsiteForm(forms.Form):
    website = forms.URLField(
        required=False,    # because we'll only save those that are there anyway
        #saves NewStudentPageContactsWebsite
    )
WebsiteFormset = formset_factory(WebsiteForm, extra=1, formset=RequiredFormSet)


################################################################################
## Academic details

class ProfileAcademicDetailsForm(forms.Form):

    funding = forms.CharField(
        max_length=255, required=False,
        help_text=help_text('rca.NewStudentPage', 'funding', default="Please include major funding bodies, including research councils.")
    )
    previous_degree = forms.CharField(
        #multiple values?
        #saves to NewStudentPagePreviousDegree
    )
    exhibitions = forms.CharField(
        #multiple values?
        #saves to NewStudentPageExhibition
    )
    awards = forms.CharField(
        #multiple values?
        #saves to NewStudentPageAward
    )
    publications = forms.CharField(
        #multiple values?
        #saves to NewStudentPagePublication
    )
    conferences = forms.CharField(
        #multiple values?
        #saves to NewStudentPageConference
    )

