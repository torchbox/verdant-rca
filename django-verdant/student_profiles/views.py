
import re
import unicodedata
import json

from django import forms
from django.http import Http404, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from wagtail.wagtailcore.models import Page
from rca.models import NewStudentPage
from rca.models import NewStudentPageContactsEmail, NewStudentPageContactsPhone, NewStudentPageContactsWebsite
from rca.models import NewStudentPagePreviousDegree, NewStudentPageExhibition, NewStudentPageAward, NewStudentPagePublication, NewStudentPageConference
from rca.models import NewStudentPageShowCarouselItem, NewStudentPageShowCollaborator, NewStudentPageShowSponsor
from rca.models import RcaImage

from .forms import ProfileBasicForm, ProfileBasicNewForm, EmailFormset, PhoneFormset, WebsiteFormset
from .forms import ProfileAcademicDetailsForm, PreviousDegreesFormset, ExhibitionsFormset, AwardsFormset, PublicationsFormset, ConferencesFormset
from .forms import MADetailsForm, MAShowDetailsForm, MAShowCarouselItemFormset, MACollaboratorFormset, MASponsorFormset

from .forms import ImageForm

# this is the ID of the page where new student pages are added as children
# MAKE SURE IT IS CORRECT FOR YOUR INSTANCE!
NEW_STUDENT_PAGE_INDEX_ID = 6201


################################################################################
## LDAP data extraction functions

def user_is_ma(request):
    """Determine whether a user is an MA user and should be able to edit their MA page."""
    # TODO: read this from LDAP
    return True

def user_is_mphil(request):
    """Determine whether a user is an MPhil user and should be able to edit their MPhil page."""
    # TODO: read this from LDAP
    return False

def user_is_phd(request):
    """Determine whether a user is an PhD user and should be able to edit their PhD page."""
    # TODO: read this from LDAP
    return False

def profile_is_in_show(profile_page):
    """Determine whether this user is in the show or not."""
    return profile_page.ma_in_show or profile_page.mphil_in_show or profile_page.phd_in_show


################################################################################
## helper functions

def slugify(value):
    """
    TODO: documentation
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '-', value)

#    save_multiple(page,         'show_collaborators', scf, 'name',  NewStudentPageShowCollaborator)
def save_multiple(profile_page, fieldname, formset, form_fieldname, field_model):
    """
    TODO: documentation
    """
    manager = getattr(profile_page, fieldname)
    for item in manager.all():
        del item
    for values in formset.cleaned_data:
        if values and values.get(form_fieldname, '').strip():
            f = manager.create(**{
                'page': profile_page,
                form_fieldname: values.get(form_fieldname).strip()
            })
            


def initial_context(request, page_id):
    """Context data that (almost) every view here needs."""
    data = {
        'is_ma': user_is_ma(request),
        'is_mphil': user_is_mphil(request),
        'is_phd': user_is_phd(request),
    }

    profile_page = get_object_or_404(NewStudentPage, owner=request.user, id=page_id).get_latest_revision_as_page()
    data['page_id'] = page_id
    data['is_in_show'] = profile_is_in_show(profile_page)
    return data, profile_page


################################################################################
## view functions

@login_required
def overview(request):
    """
    Profile overview page, probably unnecessary
    """
    data = {}

    data['profile_pages'] = NewStudentPage.objects.filter(owner=request.user)

    return render(request, 'student_profiles/overview.html', data)


@login_required
def basic_profile(request, page_id=None):
    """Basic profile creation/editing page"""
    data = {
        'is_ma': user_is_ma(request),
        'is_mphil': user_is_mphil(request),
        'is_phd': user_is_phd(request),
    }

    if page_id is None:
        profile_page = NewStudentPage(owner=request.user)
        form_class = ProfileBasicNewForm
        data['basic_form'] = ProfileBasicNewForm()
        data['email_formset'] = EmailFormset(prefix='email')
        data['phone_formset'] = PhoneFormset(prefix='phone')
        data['website_formset'] = WebsiteFormset(prefix='website')
    else:
        profile_page = get_object_or_404(NewStudentPage, owner=request.user, id=page_id).get_latest_revision_as_page()
        data['page_id'] = page_id
        form_class = ProfileBasicForm
        data['basic_form'] = ProfileBasicForm(instance=profile_page)
        data['email_formset'] = EmailFormset(
            prefix='email',
            initial=[{'email': x.email} for x in profile_page.emails.all()]
        )
        data['phone_formset'] = PhoneFormset(
            prefix='phone',
            initial=[{'phone': x.phone} for x in profile_page.phones.all()]
        )
        data['website_formset'] = WebsiteFormset(
            prefix='website',
            initial=[{'website': x.website} for x in profile_page.websites.all()]
        )

    if request.method == 'POST':
        data['basic_form'] = basic_form = form_class(request.POST, request.FILES)
        data['email_formset'] = email_formset = EmailFormset(request.POST, prefix='email')
        data['phone_formset'] = phone_formset = PhoneFormset(request.POST, prefix='phone')
        data['website_formset'] = website_formset = WebsiteFormset(request.POST, prefix='website')
        if basic_form.is_valid() and email_formset.is_valid() and phone_formset.is_valid() and website_formset.is_valid():
            bcd = basic_form.cleaned_data
            
            profile_page.title = u'{} {}'.format(bcd['first_name'], bcd['last_name'])
            profile_page.slug = slugify(profile_page.title)
            
            if page_id is None:
                # the following is the page where the new student pages are added as children
                # MAKE SURE THIS IS THE CORRECT ID!
                profile_page.live = False
                Page.objects.get(id=NEW_STUDENT_PAGE_INDEX_ID).add_child(instance=profile_page)
            else:
                profile_page.has_unpublished_changes = True

            if Page.objects.exclude(id=profile_page.id).filter(slug=profile_page.slug).exists():
                profile_page.slug = '{}-{}'.format(
                    slugify(profile_page.title),
                    profile_page.id,
                )
            
            profile_page.first_name = bcd['first_name']
            profile_page.last_name = bcd['last_name']
            
            profile_page.statement = bcd['statement']

            # we do NOT process the profile image here because that was already done by the asynchronous handler
            # possible problem: what if the user does not have javascript or the other upload handler didn't work?
            
            profile_page.emails = [
                NewStudentPageContactsEmail(email=f['email']) for f in email_formset.cleaned_data if f.get('email')
            ]
            profile_page.phones = [
                NewStudentPageContactsPhone(phone=f['phone']) for f in phone_formset.cleaned_data if f.get('phone')
            ]
            profile_page.websites = [
                NewStudentPageContactsWebsite(website=f['website']) for f in website_formset.cleaned_data if f.get('website')
            ]
            
            revision = profile_page.save_revision(
                user=request.user,
                submitted_for_moderation=False,
            )

            return redirect('student-profiles:edit-basic', page_id=profile_page.id)

    return render(request, 'student_profiles/basic.html', data)



@login_required
def academic_details(request, page_id=None):
    """
    Academic details editing page.
    """
    data, profile_page = initial_context(request, page_id)
    
    data['academic_form'] = ProfileAcademicDetailsForm(instance=profile_page)
    
    def make_formset(title, formset_class, relname, form_attr_name, model_attr_name=None):
        
        model_attr_name = model_attr_name or form_attr_name
        
        data[relname + '_formset'] = formset_class(
            prefix=relname,
            initial=[{form_attr_name: getattr(x, model_attr_name)} for x in getattr(profile_page, relname).all()],
        )
        data[relname + '_formset'].title = title

    make_formset(
        'Previous degrees',
        PreviousDegreesFormset, 'previous_degrees',
        'degree',
    )

    make_formset(
        'Exhibitions',
        ExhibitionsFormset, 'exhibitions',
        'exhibition',
    )

    make_formset(
        'Awards',
        AwardsFormset, 'awards',
        'award',
    )

    make_formset(
        'Publications',
        PublicationsFormset, 'publications',
        'name',
    )

    make_formset(
        'Conferences',
        ConferencesFormset, 'conferences',
        'name',
    )
    
    if request.method == 'POST':
        data['academic_form'] = pf = ProfileAcademicDetailsForm(request.POST)
        data['previous_degrees_formset'] = pdfs = PreviousDegreesFormset(request.POST, prefix='previous_degrees')
        data['exhibitions_formset'] = efs = ExhibitionsFormset(request.POST, prefix='exhibitions')
        data['awards_formset'] = afs = AwardsFormset(request.POST, prefix='awards')
        data['publications_formset'] = pfs = PublicationsFormset(request.POST, prefix='publications')
        data['conferences_formset'] = cfs = ConferencesFormset(request.POST, prefix='conferences')
        
        if pf.is_valid() and pdfs.is_valid() and efs.is_valid() and pfs.is_valid() and cfs.is_valid():
            profile_page.funding = pf.cleaned_data['funding']
            
            profile_page.previous_degrees = [
                NewStudentPagePreviousDegree(degree=f['degree']) for f in pdfs.cleaned_data if f.get('degree')
            ]
            profile_page.exhibitions = [
                NewStudentPageExhibition(exhibition=f['exhibition']) for f in efs.cleaned_data if f.get('exhibition')
            ]
            profile_page.awards = [
                NewStudentPageAward(award=f['award']) for f in afs.cleaned_data if f.get('award')
            ]
            profile_page.publications = [
                NewStudentPagePublication(name=f['name']) for f in pfs.cleaned_data if f.get('name')
            ]
            profile_page.conferences = [
                NewStudentPageConference(name=f['name']) for f in cfs.cleaned_data if f.get('name')
            ]
            
            revision = profile_page.save_revision(
                user=request.user,
                submitted_for_moderation=False,
            )
        
            return redirect('student-profiles:edit-academic', page_id=profile_page.id)
    
    return render(request, 'student_profiles/academic_details.html', data)


@login_required
def ma_details(request, page_id):
    if not user_is_ma(request):
        raise Http404("You cannot view MA details because you're not in the MA programme.")
    data, profile_page = initial_context(request, page_id)

    data['ma_form'] = MADetailsForm(instance=profile_page)

    if request.method == 'POST':
        data['ma_form'] = form = MADetailsForm(request.POST, instance=profile_page, )

        if form.is_valid():
            page = form.save(commit=False)
            
            revision = page.save_revision(
                user=request.user,
                submitted_for_moderation=False,
            )
            

        return redirect('student-profiles:edit-ma', page_id=page_id)

    return render(request, 'student_profiles/ma_details.html', data)


@login_required
def ma_show_details(request, page_id):
    if not user_is_ma(request):
        raise Http404("You cannot view MA show details because you're not in the MA programme.")

    data, profile_page = initial_context(request, page_id)

    def make_formset(title, formset_class, relname, form_attr_name, model_attr_name=None):
        
        model_attr_name = model_attr_name or form_attr_name
        
        data[relname + '_formset'] = formset_class(
            prefix=relname,
            initial=[{form_attr_name: getattr(x, model_attr_name)} for x in getattr(profile_page, relname).all()],
        )
        
        data[relname + '_formset'].title = title

    data['show_form'] = MAShowDetailsForm(instance=profile_page)
    
    carousel_initial = [
        {
            'item_type': 'image' if c.image_id is not None else 'video',
            'image_id': c.image_id, 'overlay_text': c.overlay_text, 'embedly_url': c.embedly_url, 'poster_image_id': c.poster_image_id
        }
        for c in profile_page.show_carousel_items.all()
    ]
    data['carouselitem_formset'] = MAShowCarouselItemFormset(prefix='carousel', initial=carousel_initial)
    
    make_formset('Collaborator', MACollaboratorFormset, 'show_collaborators', 'name')
    make_formset('Sponsor', MASponsorFormset, 'show_sponsors', 'name')

    if request.method == 'POST':
        data['show_form'] = sf = MAShowDetailsForm(request.POST, instance=profile_page)
        data['carouselitem_formset'] = scif = MAShowCarouselItemFormset(request.POST, prefix='carousel', initial=carousel_initial)
        data['show_collaborators_formset'] = scf = MACollaboratorFormset(request.POST, prefix='show_collaborators')
        data['show_sponsors_formset'] = ssf = MASponsorFormset(request.POST, prefix='show_sponsors')
        
        if sf.is_valid() and scif.is_valid() and scf.is_valid() and ssf.is_valid():

            page = sf.save(commit=False)

            carousel_items = [
                {k:v for k,v in f.items() if k != 'item_type'}
                for f in scif.cleaned_data if f.get('item_type') and (f.get('image_id') or f.get('embedly_url'))
            ]
            print carousel_items
            page.show_carousel_items = [
                NewStudentPageShowCarouselItem(**item) for item in carousel_items
            ]
            
            page.show_collaborators = [
                NewStudentPageShowCollaborator(name=f['name'].strip()) for f in scf.cleaned_data if f.get('name')
            ]
            page.show_sponsors = [
                NewStudentPageShowSponsor(name=f['name'].strip()) for f in ssf.cleaned_data if f.get('name')
            ]
            
            revision = page.save_revision(
                user=request.user,
                submitted_for_moderation=False,
            )

            return redirect('student-profiles:edit-ma-show', page_id=page_id)

    return render(request, 'student_profiles/ma_show_details.html', data)


@require_POST
@login_required
def image_upload(request, page_id, field=None):
    
    data, profile_page = initial_context(request, page_id)
    
    form = ImageForm(request.POST, request.FILES)
    if form.is_valid():
        r = RcaImage.objects.create(
            file=form.cleaned_data['image'],
            uploaded_by_user=request.user,
        )
        
        if field:
            # set the field to the image
            setattr(profile_page, field, r)
            revision = profile_page.save_revision(
                user=request.user,
                submitted_for_moderation=False,
            )
        
        return HttpResponse('{{"ok": true, "id": {} }}'.format(r.id), content_type='application/json')
    else:
        print form.errors.items()
        errors = ', '.join(', '.join(el) for el in form.errors.values())
        res = {'ok': False, 'errors': errors}
        return HttpResponse(json.dumps(res), content_type='application/json')
