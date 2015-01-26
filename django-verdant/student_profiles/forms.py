# -*- encoding: utf-8 -*-

from django import forms
from django.forms.formsets import formset_factory, BaseFormSet
from django.template.defaultfilters import filesizeformat

from PIL import image

from wagtail.wagtailcore.fields import RichTextArea

from rca.help_text import help_text
from rca.models import NewStudentPage, NewStudentPageShowCarouselItem
from rca.models import NewStudentPageMPhilCollaborator, NewStudentPageMPhilSponsor, NewStudentPageMPhilSupervisor
from rca.models import NewStudentPagePhDCollaborator, NewStudentPagePhDSponsor, NewStudentPagePhDSupervisor
from rca.models import RcaImage, StaffPage
from rca.models import SCHOOL_PROGRAMME_MAP, ALL_PROGRAMMES

################################################################################
## internal classes

class OrderedFormset(BaseFormSet):
    
    def __init__(self, *args, **kwargs):
        #print args, kwargs

        #for index, value in enumerate(kwargs.get('initial', {})):
        #    value['order'] = index

        
        super(OrderedFormset, self).__init__(*args, **kwargs)
    
    def clean(self):
        """Cleans the form and orders it by the hidden added order field."""
        
        order = lambda item: item.get('order', 10000)   # yes, 10000 = infinity!
        if hasattr(self, 'cleaned_data'):
            self.ordered_data = sorted(self.cleaned_data, key=order)
        
        return

    def add_fields(self, form, index):
        """Add the necessary hidden ordering field."""
        form.fields['order'] = forms.IntegerField(
            initial=index + 1,
            required=False,
            widget=forms.HiddenInput(attrs={'class': 'order-value'})
        )


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
                rendition = image.get_rendition('max-150x150')
                preview = """
                    <img src="{url}" width="{width}" height="{height}" style="width: auto;">
                """.format(
                    url=rendition.url,
                    width=rendition.width, height=rendition.height,
                )
            except ValueError:
                pass
            except IOError:
                pass
        
        return """
            <div id="{name}" class="image-uploader-block" data-url="image/">
                <div class="preview" style="display: {preview_display};">
                    {preview}
                    <div class="progress">
                        <div class="bar" style="width: 0%; height: 3px; background: #0096ff;"></div>
                    </div> 
                    <i class="icon clearbutton action ion-android-delete" {hidden_clear} title="Remove"></i>
                </div>
                <div class="dropzone">Drop file here</div>
                <input type="hidden" id="id_{name}_val" name="{name}_val" value="{value_id}">

            </div>""".format(
                name=name,
                preview=preview, preview_display='block' if preview else 'none',
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

    def __init__(self, *args, **kwargs):

        self.max_size = None
        self.min_dim = None
        if 'max_size' in kwargs:
            self.max_size = kwargs.pop('max_size')
        if 'min_dim' in kwargs:
            self.min_dim = kwargs.pop('min_dim')

        super(ImageForm, self).__init__(*args, **kwargs)

    image = forms.ImageField()

    def clean_image(self):
        img = self.cleaned_data['image']
        if self.max_size and img.size > self.max_size:
            raise forms.ValidationError(u'Please keep file size under 10MB. Current file size {}'.format(filesizeformat(img.size)))

        if self.min_dim:
            dt = Image.open(img)
            minX, minY = self.min_dim
            width, height = dt.size
            if (width < minX or height < minY) and (height < minX or width < minY):
                raise forms.ValidationError(u'Minimum image size is {}x{} pixels.'.format(minX, minY))

        return img



################################################################################
## Starting out

class StartingForm(forms.ModelForm):

    class Meta:
        model = NewStudentPage
        fields = ['first_name', 'last_name']



################################################################################
## Basic Profile

class ProfileBasicForm(forms.ModelForm):
    
    profile_image = forms.IntegerField(
        required=False,
        help_text=help_text('rca.NewStudentPage', 'profile_image', default="Self-portrait image, 500x500px"),
        widget=ImageInput,
    )

    def clean_profile_image(self):
        if self.cleaned_data['profile_image']:
            return RcaImage.objects.get(id=self.cleaned_data['profile_image'])
        return None

    def clean_twitter_handle(self):
        if self.cleaned_data.get('twitter_handle'):
            handle = self.cleaned_data.get('twitter_handle', '')
            if handle.startswith('@'):
                return handle[1:]
            else:
                return handle
        else:
            return ''

    class Meta:
        model = NewStudentPage
        fields = ['title', 'first_name', 'last_name', 'twitter_handle', 'profile_image', 'statement']


class EmailForm(forms.Form):
    #saves to NewStudentPageContactsEmail
    email = forms.EmailField(
        required=False,    # because we'll only save those that are there anyway
        help_text=help_text('rca.NewStudentPageContactsEmail', 'email', default="Students can use personal email as well as firstname.surname@network.rca.ac.uk")
    )
EmailFormset = formset_factory(EmailForm, extra=1, formset=OrderedFormset)

class PhoneForm(forms.Form):
    #saves to NewStudentPageContactsPhone
    phone = PhoneNumberField(
        required=False,    # because we'll only save those that are there anyway
        help_text=help_text('rca.NewStudentPageContactsPhone', 'phone', default="UK mobile e.g. 07XXX XXXXXX or overseas landline, e.g. +33 (1) XXXXXXX")
    )
PhoneFormset = formset_factory(PhoneForm, extra=1, formset=OrderedFormset)
PhoneFormset.help_text = 'Enter your phone number(s) in international format with country code: +44 (0) 12345 678910'

class WebsiteForm(forms.Form):
    #saves to NewStudentPageContactsWebsite
    website = forms.URLField(
        required=False,    # because we'll only save those that are there anyway
        error_messages={'invalid': 'Please enter a full URL, including the ‘http://’!'},
        widget=forms.TextInput,
    )

    def clean_website(self):
        website = self.cleaned_data.get('website')
        if not website:
            return None
        if not website.startswith(u'http://') or website.startswith(u'https://'):
            return u'http://' + website
        else:
            return website

WebsiteFormset = formset_factory(WebsiteForm, extra=1, formset=OrderedFormset)
WebsiteFormset.help_text = 'Paste in the URL of the website in full, including the ‘http://’'


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
PreviousDegreesFormset = formset_factory(PreviousDegreeForm, extra=1, formset=OrderedFormset)

class ExhibitionForm(forms.Form):
    #saves to NewStudentPageExhibition
    exhibition = forms.CharField(
        required=False,
        help_text=help_text('rca.NewStudentPageExhibition', 'exhibition', default="Please include exhibition title, gallery, city and year, separated by commas"),
    )
ExhibitionsFormset = formset_factory(ExhibitionForm, extra=1, formset=OrderedFormset)

class ExperienceForm(forms.Form):
    experience = forms.CharField(
        max_length=255, required=False,
        help_text=help_text('rca.NewStudentPageExperience', 'experience', default="Please include job title, company name, city and year(s), separated by commas"),
    )
ExperiencesFormset = formset_factory(ExperienceForm, extra=1, formset=OrderedFormset)

class AwardsForm(forms.Form):
    #saves to NewStudentPageAward
    award = forms.CharField(
        required=False,
        help_text=help_text('rca.NewStudentPageAward', 'award', default="Please include prize, award title and year, separated by commas"),
    )
AwardsFormset = formset_factory(AwardsForm, extra=1, formset=OrderedFormset)
    
class PublicationsForm(forms.Form):
    #saves to NewStudentPagePublication
    name = forms.CharField(
        required=False,
        help_text=help_text('rca.NewStudentPagePublication', 'name', default="Please include author (if not you), title of article, title of publication, issue number, year, pages, separated by commas"),
    )
PublicationsFormset = formset_factory(PublicationsForm, extra=1, formset=OrderedFormset)

class ConferencesForm(forms.Form):
    #saves to NewStudentPageConference
    name = forms.CharField(
        required=False,
        help_text=help_text('rca.NewStudentPageConference', 'name', default="Please include paper, title of conference, institution, date, separated by commas"),
    )
ConferencesFormset = formset_factory(ConferencesForm, extra=1, formset=OrderedFormset)


################################################################################
## postcard upload

class PostcardUploadForm(forms.ModelForm):
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
            'postcard_image',
        ]


################################################################################
## custom school and programme choices for 2015

SCHOOL_CHOICES = (
    ('', '---------'),
    ('schoolofarchitecture', 'School of Architecture'),
    ('schoolofcommunication', 'School of Communication'),
    ('schoolofdesign', 'School of Design'),
    ('schooloffineart', 'School of Fine Art'),
    ('schoolofhumanities', 'School of Humanities'),
    ('schoolofmaterial', 'School of Material'),
)

PROGRAMME_CHOICES_2015 = (('', '---------'), ) + tuple(sorted([
    (
        2015, tuple([
                    (programme, dict(ALL_PROGRAMMES)[programme])
                    for programme
                    in sorted(set(sum(SCHOOL_PROGRAMME_MAP['2014'].values(), [])))
                ])
    )
], reverse=True))


################################################################################
## MA details

class MADetailsForm(forms.ModelForm):

    ma_in_show = forms.BooleanField(
        label='In show',
        required=False,
        help_text="Please tick only if you're in the Show this academic year.",
    )

    ma_graduation_year = forms.IntegerField(
        label='Graduation year',
        min_value=1950, max_value=2050,
        required=False,
        help_text=help_text('rca.NewStudentPage', 'ma_graduation_year'),
    )

    ma_school = forms.ChoiceField(
        label="School", help_text=help_text('rca.NewStudentPage', 'ma_school'),
        choices=SCHOOL_CHOICES,
        required=False,
    )

    ma_programme = forms.ChoiceField(
        label="Programme",
        choices=PROGRAMME_CHOICES_2015,
        required=False,
    )

    def clean_ma_graduation_year(self):
        if self.cleaned_data['ma_graduation_year']:
            return self.cleaned_data['ma_graduation_year']
        else:
            return ''

    class Meta:
        model = NewStudentPage
        fields = [
            'ma_in_show',
            'ma_school', 'ma_programme',
            'ma_graduation_year',
            'ma_specialism',
        ]


class MAShowDetailsForm(forms.ModelForm):

    class Meta:
        model = NewStudentPage
        fields = [
            'show_work_type',
            'show_work_title',
            'show_work_location',
            'show_work_description',
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

    # image type fields (there are a lot of them!)
    title = forms.CharField(max_length=255, required=False, label='Title', )
    alt = forms.CharField(max_length=255, required=False, help_text=help_text('rca.RcaImage', 'alt'))
    creator = forms.CharField(max_length=255, required=False, help_text=help_text('rca.RcaImage', 'creator') + 'If this work was a collaboration with others, list them here after your own name in brackets.')
    year = forms.CharField(max_length=255, required=False, help_text=help_text('rca.RcaImage', 'year'))
    medium = forms.CharField(max_length=255, required=False, help_text=help_text('rca.RcaImage', 'medium'))
    dimensions = forms.CharField(max_length=255, required=False, help_text=help_text('rca.RcaImage', 'dimensions'))
    photographer = forms.CharField(max_length=255, required=False, help_text=help_text('rca.RcaImage', 'photographer'))

    embedly_url = forms.URLField(
        label='Vimeo URL',
        required=False,
        help_text='You cannot upload a video directly; you must upload any video content to Vimeo, and you can then paste the URL to your video in here.',
    )
    poster_image_id = forms.IntegerField(
        label='Poster image',
        required=False,
        help_text='Add a still image as a placeholder for your video when it is not playing.',
        widget=ImageInput,
    )

    def clean_title(self):
        if self.cleaned_data.get('item_type') == 'image' and self.cleaned_data.get('image_id') and not self.cleaned_data.get('title'):
            raise forms.ValidationError('This field is required.')
        else:
            return self.cleaned_data.get('title', '')
MAShowCarouselItemFormset = formset_factory(form=MAShowCarouselItemForm, extra=1, formset=OrderedFormset, max_num=12, validate_max=True)

class MACollaboratorForm(forms.Form):
    #saves to NewStudentPageShowCollaborator
    name = forms.CharField(
        required=False,
        help_text=help_text('rca.NewStudentPageShowCollaborator', 'name', default="Please include collaborator's name and programme (if RCA), separated by commas")
    )
MACollaboratorFormset = formset_factory(MACollaboratorForm, extra=1, formset=OrderedFormset)
    
class MASponsorForm(forms.Form):
    #saves to NewStudentPageShowSponsor
    name = forms.CharField(
        required=False,
        help_text=help_text('rca.NewStudentPageShowSponsor', 'name', default="Please list companies and individuals that have provided financial or in kind sponsorship for your final project, separated by commas")
    )
MASponsorFormset = formset_factory(MASponsorForm, extra=1, formset=OrderedFormset)


# MPhil and PhD forms
class MPhilForm(forms.ModelForm):

    mphil_school = forms.ChoiceField(
        label="School", help_text=help_text('rca.NewStudentPage', 'mphil_school'),
        choices=SCHOOL_CHOICES,
        required=False,
    )

    mphil_programme = forms.ChoiceField(
        label="Programme", help_text=help_text('rca.NewStudentPage', 'mphil_programme'),
        choices=PROGRAMME_CHOICES_2015,
        required=False,
    )

    mphil_start_year = forms.IntegerField(
        label='Start year',
        min_value=1950, max_value=2050,
        required=False,
        help_text=help_text('rca.NewStudentPage', 'mphil_start_year'),
    )
    mphil_graduation_year = forms.IntegerField(
        label='Graduation year',
        min_value=1950, max_value=2050,
        required=False,
        help_text='If unknown, enter current year',
    )

    def clean_mphil_start_year(self):
        if self.cleaned_data['mphil_start_year']:
            return self.cleaned_data['mphil_start_year']
        else:
            return ''
    def clean_mphil_graduation_year(self):
        if self.cleaned_data['mphil_graduation_year']:
            return self.cleaned_data['mphil_graduation_year']
        else:
            return ''


    class Meta:
        model = NewStudentPage
        fields = [
            'mphil_in_show',
            'mphil_school', 'mphil_programme',
            'mphil_start_year',
            'mphil_graduation_year',
        ]


class MPhilShowForm(forms.ModelForm):
    class Meta:
        model = NewStudentPage
        fields = [
            'mphil_dissertation_title',
            'mphil_statement',
            'mphil_work_location',
        ]
# carousel items as above, sponsor and collaborator almost as above

# we create new forms here because the labels and help_texts are slightly different
class MPhilCollaboratorForm(forms.ModelForm):
    class Meta:
        model = NewStudentPageMPhilCollaborator
        fields = ['name']
MPhilCollaboratorFormset = formset_factory(
    MPhilCollaboratorForm,
    extra=1, formset=OrderedFormset
)
class MPhilSponsorForm(forms.ModelForm):
    class Meta:
        model = NewStudentPageMPhilSponsor
        fields = ['name']
MPhilSponsorFormset = formset_factory(
    MPhilSponsorForm,
    extra=1, formset=OrderedFormset
)
    
class MPhilSupervisorForm(forms.ModelForm):
    supervisor_type = forms.ChoiceField(
        label='Type',
        choices = (   
            ('internal', 'Internal'),
            ('other', 'Other'),
        )
    )

    supervisor = forms.ModelChoiceField(
        queryset=StaffPage.objects.all().order_by('last_name'),
        required=False,
        help_text=help_text('rca.NewStudentPageMPhilSupervisor', 'supervisor', default="Please select your RCA supervisor's profile page or enter the name of an external supervisor"),
        widget=forms.Select(attrs={'width': '100%', 'class': 'supervisor-select'}),
    )

    class Meta:
        model = NewStudentPageMPhilSupervisor
        fields = ['supervisor', 'supervisor_other']
MPhilSupervisorFormset = formset_factory(MPhilSupervisorForm, extra=1, formset=OrderedFormset)


# and the same once again with PhD instead of MPhil
class PhDForm(forms.ModelForm):

    phd_school = forms.ChoiceField(
        label="School", help_text=help_text('rca.NewStudentPage', 'phd_school'),
        choices=SCHOOL_CHOICES,
        required=False,
    )

    phd_programme = forms.ChoiceField(
        label="Programme", help_text=help_text('rca.NewStudentPage', 'phd_programme'),
        choices=PROGRAMME_CHOICES_2015,
        required=False,
    )

    phd_start_year = forms.IntegerField(
        label='Start year',
        min_value=1950, max_value=2050,
        required=False,
        help_text=help_text('rca.NewStudentPage', 'phd_start_year'),
    )
    phd_graduation_year = forms.IntegerField(
        label='Graduation year',
        min_value=1950, max_value=2050,
        required=False,
        help_text='If unknown, enter current year'
    )

    def clean_phd_start_year(self):
        if self.cleaned_data['phd_start_year']:
            return self.cleaned_data['phd_start_year']
        else:
            return ''
    def clean_phd_graduation_year(self):
        if self.cleaned_data['phd_graduation_year']:
            return self.cleaned_data['phd_graduation_year']
        else:
            return ''

    class Meta:
        model = NewStudentPage
        fields = [
            'phd_in_show',
            'phd_school', 'phd_programme',
            'phd_start_year', 'phd_graduation_year',
        ]


class PhDShowForm(forms.ModelForm):
    class Meta:
        model = NewStudentPage
        fields = [
            'phd_dissertation_title',
            'phd_statement',
            'phd_work_location',
        ]


class PhDCollaboratorForm(forms.ModelForm):
    class Meta:
        model = NewStudentPagePhDCollaborator
        fields = ['name']
PhDCollaboratorFormset = formset_factory(
    PhDCollaboratorForm,
    extra=1, formset=OrderedFormset
)
class PhDSponsorForm(forms.ModelForm):
    class Meta:
        model = NewStudentPagePhDSponsor
        fields = ['name']
PhDSponsorFormset = formset_factory(
    PhDSponsorForm,
    extra=1, formset=OrderedFormset
)
    
class PhDSupervisorForm(forms.ModelForm):
    supervisor_type = forms.ChoiceField(
        label='Type',
        choices = (   
            ('internal', 'Internal'),
            ('other', 'Other'),
        )
    )
    
    supervisor = forms.ModelChoiceField(
        queryset=StaffPage.objects.all().order_by('last_name'),
        required=False,
        help_text=help_text('rca.NewStudentPagePhDSupervisor', 'supervisor', default="Please select your RCA supervisor's profile page or enter the name of an external supervisor"),
        widget=forms.Select(attrs={'width': '100%', 'class': 'supervisor-select'}),
    )

    class Meta:
        model = NewStudentPagePhDSupervisor
        fields = ['supervisor', 'supervisor_other']
PhDSupervisorFormset = formset_factory(PhDSupervisorForm, extra=1, formset=OrderedFormset)
