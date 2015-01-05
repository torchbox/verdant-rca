from itertools import chain

from django import forms
from django.forms.formsets import formset_factory, BaseFormSet
from django.forms.models import modelformset_factory

from wagtail.wagtailcore.fields import RichTextArea

from rca.help_text import help_text
from rca.models import NewStudentPage, NewStudentPageShowCarouselItem
from rca.models import RcaImage

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


class ImageInput(forms.FileInput):

    def value_from_datadict(self, data, files, name):
        try:
            return int(data.get('{}_val'.format(name)))
        except ValueError:
            return None

    def render(self, name, value, attrs=None):
        preview = ""
        if value:
            try:
                value = int(value)
                image = RcaImage.objects.get(id=value)
                rendition = image.get_rendition('max-130x100')
                preview = """
                    <img src="{url}" width="{width}" height="{height}" style="width: auto;">
                """.format(
                    url=rendition.url,
                    width=rendition.width, height=rendition.height,
                )
            except ValueError:
                pass
        
        return """
            <div id="{name}" class="image-uploader-block" data-url="image/">
                <div class="preview" style="position: relative;">{preview}</div>
                <div class="dropzone" style="width: 200px; height: 100px;">Drop files here</div>
                <button class="clearbutton"{hidden_clear}>Clear image</button>
                <input type="hidden" id="id_{name}_val" name="{name}_val" value="{value_id}">
                <div class="progress">
                    <div class="bar" style="width: 0%; height: 18px; background: green;"></div>
                </div>
            </div>""".format(
                name=name,
                preview=preview,
                value_id=value,
                hidden_clear='' if preview else ' style="display: none;"',
            )
    


################################################################################
## Helper Forms

class ImageForm(forms.Form):
    """This is a simple form that validates a single image.
    
    This is used in validating image uploads, obviously. It's needed because we upload images not with the forms
    themselves but asynchronously by themselves.
    """
    
    image = forms.ImageField()



################################################################################
## Basic Profile

class ProfileBasicForm(forms.ModelForm):
    
    profile_image = forms.IntegerField(
        required=False,
        help_text=help_text('rca.NewStudentPage', 'profile_image', default="Self-portrait image, 500x500px"),
        widget=ImageInput,
    )

    def clean_profile_image(self):
        return self.instance.profile_image

    class Meta:
        model = NewStudentPage
        fields = ['first_name', 'last_name', 'profile_image', 'statement']


class ProfileBasicNewForm(ReadonlyFormMixin, forms.ModelForm):

    profile_image = forms.ImageField(
        help_text='You must save this profile first before you can add an image.'
    )
    profile_image.readonly = True

    class Meta:
        model = NewStudentPage
        fields = ['first_name', 'last_name', 'statement']


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


################################################################################
## MA details

class MADetailsForm(forms.ModelForm):
    
    class Meta:
        model = NewStudentPage
        fields = [
            'ma_in_show',
            'ma_school', 'ma_programme',
            'ma_graduation_year',
            'ma_specialism',
        ]


class MAShowDetailsForm(forms.ModelForm):
    
    postcard_image = forms.IntegerField(
        label='Postcard image',
        required=False,
        help_text=help_text('rca.NewStudentPage', 'postcard_image', default="Please upload images sized to A6 plus 2mm 'bleed' (152 x 109mm or 1795 x 1287px @ 300 dpi) - this must be uploaded at the correct size for printed postcards"),
        widget=ImageInput,
    )
    
    def clean_postcard_image(self):
        try:
            return RcaImage.objects.get(id=self.cleaned_data.get('postcard_image'))
        except RcaImage.DoesNotExist:
            return None
    
    class Meta:
        model = NewStudentPage
        fields = [
            'show_work_type',
            'show_work_title',
            'show_work_location',
            'show_work_description',
            'postcard_image',
        ]

class MAShowCarouselItemForm(forms.Form):

    item_type = forms.ChoiceField(
        choices = (   
            ('image', 'Image'),    # if you change these values, you must also change the values in the javascript and in the views!
            ('video', 'Video'),
        )
    )

    image_id = forms.IntegerField(   # name is _id because that's what's going to be saved
        label='Image',
        required=False,
        help_text=help_text('rca.CarouselItemFields', 'image'),
        widget=ImageInput,
    )
    overlay_text = forms.CharField(
        max_length=255,
        required=False,
        help_text=help_text('rca.CarouselItemFields', 'overlay_text')
    )
    
    embedly_url = forms.URLField(
        label='Vimeo URL',
        required=False,
        help_text=help_text('rca.CarouselItemFields', 'embedly_url'),
    )
    poster_image_id = forms.IntegerField(
        label='Poster image',
        required=False,
        help_text=help_text('rca.CarouselItemFields', 'poster_image'),
        widget=ImageInput,
    )
MAShowCarouselItemFormset = formset_factory(form=MAShowCarouselItemForm, extra=1)

class MACollaboratorForm(forms.Form):
    #saves to NewStudentPageShowCollaborator
    name = forms.CharField(
        required=False,
        help_text=help_text('rca.NewStudentPageShowCollaborator', 'name', default="Please include collaborator's name and programme (if RCA), separated by commas")
    )
MACollaboratorFormset = formset_factory(MACollaboratorForm, extra=1)
    
class MASponsorForm(forms.Form):
    #saves to NewStudentPageShowSponsor
    name = forms.CharField(
        required=False,
        help_text=help_text('rca.NewStudentPageShowSponsor', 'name', default="Please list companies and individuals that have provided financial or in kind sponsorship for your final project, separated by commas")
    )
MASponsorFormset = formset_factory(MASponsorForm, extra=1)