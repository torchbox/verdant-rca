from itertools import chain

from django import forms
from django.forms.formsets import formset_factory, BaseFormSet

from rca.help_text import help_text
from rca.models import NewStudentPage

################################################################################
## internal classes

class ReadonlyFormMixin(object):
    """Form that allows read-only fields.
    
    To make a field readonly, simply set the property `.readonly = True` on the
    field. The initial value of the field is copied into `cleaned_data`.
    """

    def __init__(self, *args, **kwargs):
        super(ReadonlyFormMixin, self).__init__(*args, **kwargs)
        
        for field in self.fields:
            ffield = self[field].field
            if getattr(ffield, 'readonly', False):
                ffield.required = False

    def clean(self):
        cleaned_data = super(ReadonlyFormMixin, self).clean()

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
        'invalid': 'Please enter a valid telephone number. Phone numbers can only contain digits, spaces, "+", parens and dashes.',
    }

    def __init__(self, *args, **kwargs):
        super(PhoneNumberField, self).__init__(
            r'^[+0][()\d -]+$',
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

class ProfileBasicForm(ReadonlyFormMixin, forms.ModelForm):
    
    """
    first_name = forms.CharField(
        max_length=255, help_text=help_text('rca.NewStudentPage', 'first_name')
    )
    last_name = forms.CharField(
        max_length=255, help_text=help_text('rca.NewStudentPage', 'last_name')
    )
    
    profile_image = forms.ImageField(
        required=False,
        help_text=help_text('rca.NewStudentPage', 'profile_image', default="Self-portrait image, 500x500px"),
    )
    # saves as: models.ForeignKey('rca.RcaImage')
    
    statement = RichTextField(
        required=False,
        help_text=help_text('rca.NewStudentPage', 'statement'),
    )
    """
    
    profile_image = forms.ImageField(
        required=False,
        help_text=help_text('rca.NewStudentPage', 'profile_image', default="Self-portrait image, 500x500px"),
    )
    # saves as: models.ForeignKey('rca.RcaImage')
    
    # remove this later!
    in_show = BooleanField(initial=True)
    in_show.readonly = True
    
    class Meta:
        model = NewStudentPage
        fields = ['first_name', 'last_name', 'profile_image', 'statement']
    

class EmailForm(forms.Form):
    #saves to NewStudentPageContactsEmail
    email = forms.EmailField(
        required=False,    # because we'll only save those that are there anyway
        help_text=help_text('rca.NewStudentPageContactsEmail', 'email', default="Students can use personal email as well as firstname.surname@network.rca.ac.uk")
    )
EmailFormset = formset_factory(EmailForm, extra=1)
    
class PhoneForm(forms.Form):
    #saves to NewStudentPageContactsPhone
    phone = PhoneNumberField(
        required=False,    # because we'll only save those that are there anyway
        help_text=help_text('rca.NewStudentPageContactsPhone', 'phone', default="UK mobile e.g. 07XXX XXXXXX or overseas landline, e.g. +33 (1) XXXXXXX")
    )
PhoneFormset = formset_factory(PhoneForm, extra=1)

class WebsiteForm(forms.Form):
    #saves to NewStudentPageContactsWebsite
    website = forms.URLField(
        required=False,    # because we'll only save those that are there anyway
    )
WebsiteFormset = formset_factory(WebsiteForm, extra=1)


################################################################################
## Academic details

class ProfileAcademicDetailsForm(forms.ModelForm):
    
    class Meta:
        model = NewStudentPage
        fields = ['funding']
    
class PreviousDegreeForm(forms.Form):
    #saves to NewStudentPagePreviousDegree
    degree = forms.CharField(
        required=False,
        help_text=help_text('rca.NewStudentPagePreviousDegree', 'degree', default="Please include the degree level, subject, institution name and year of graduation, separated by commas"),
    )
PreviousDegreesFormset = formset_factory(PreviousDegreeForm, extra=1)

class ExhibitionForm(forms.Form):
    #saves to NewStudentPageExhibition
    exhibition = forms.CharField(
        required=False,
        help_text=help_text('rca.NewStudentPageExhibition', 'exhibition', default="Please include exhibition title, gallery, city and year, separated by commas"),
    )
ExhibitionsFormset = formset_factory(ExhibitionForm, extra=1)

class AwardsForm(forms.Form):
    #saves to NewStudentPageAward
    award = forms.CharField(
        required=False,
        help_text=help_text('rca.NewStudentPageAward', 'award', default="Please include prize, award title and year, separated by commas"),
    )
AwardsFormset = formset_factory(AwardsForm, extra=1)
    
class PublicationsForm(forms.Form):
    #saves to NewStudentPagePublication
    name = forms.CharField(
        required=False,
        help_text=help_text('rca.NewStudentPagePublication', 'name', default="Please include author (if not you), title of article, title of publication, issue number, year, pages, separated by commas"),
    )
PublicationsFormset = formset_factory(PublicationsForm, extra=1)

class ConferencesForm(forms.Form):
    #saves to NewStudentPageConference
    name = forms.CharField(
        required=False,
        help_text=help_text('rca.NewStudentPageConference', 'name', default="Please include paper, title of conference, institution, date, separated by commas"),
    )
ConferencesFormset = formset_factory(ConferencesForm, extra=1)

