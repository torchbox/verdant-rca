
import re
import unicodedata
import json

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from wagtail.wagtailcore.models import Page
from rca.models import NewStudentPage
from rca.models import NewStudentPageContactsEmail, NewStudentPageContactsPhone, NewStudentPageContactsWebsite
from rca.models import NewStudentPagePreviousDegree, NewStudentPageExhibition, NewStudentPageExperience, NewStudentPageAward, NewStudentPagePublication, NewStudentPageConference
from rca.models import NewStudentPageShowCarouselItem, NewStudentPageShowCollaborator, NewStudentPageShowSponsor
from rca.models import NewStudentPageMPhilCarouselItem, NewStudentPageMPhilCollaborator, NewStudentPageMPhilSponsor, NewStudentPageMPhilSupervisor
from rca.models import NewStudentPagePhDCarouselItem, NewStudentPagePhDCollaborator, NewStudentPagePhDSponsor, NewStudentPagePhDSupervisor
from rca.models import RcaImage

from .forms import StartingForm
from .forms import ProfileBasicForm, EmailFormset, PhoneFormset, WebsiteFormset
from .forms import ProfileAcademicDetailsForm, PreviousDegreesFormset, ExperiencesFormset, ExhibitionsFormset, AwardsFormset, PublicationsFormset, ConferencesFormset
from .forms import MADetailsForm, MAShowDetailsForm, MAShowCarouselItemFormset, MACollaboratorFormset, MASponsorFormset
from .forms import MPhilForm, MPhilCollaboratorFormset, MPhilSponsorFormset, MPhilSupervisorFormset
from .forms import PhDForm, PhDCollaboratorFormset, PhDSponsorFormset, PhDSupervisorFormset

from .forms import ImageForm

# this is the ID of the page where new student pages are added as children
# MAKE SURE IT IS CORRECT FOR YOUR INSTANCE!
NEW_STUDENT_PAGE_INDEX_ID = 6201


################################################################################
## LDAP data extraction functions

def user_is_ma(request):
    """Determine whether a user is an MA user and should be able to edit their MA page."""
    return request.user.groups.filter(name='MA Students').exists()

def user_is_mphil(request):
    """Determine whether a user is an MPhil user and should be able to edit their MPhil page."""
    return request.user.groups.filter(name='MPhil Students').exists()

def user_is_phd(request):
    """Determine whether a user is an PhD user and should be able to edit their PhD page."""
    return request.user.groups.filter(name='PhD Students').exists()

def profile_is_in_show(request, profile_page):
    """Determine whether this user is in the show or not."""
    return user_is_ma(request) and profile_page.ma_in_show


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

    data['page'] = profile_page = get_object_or_404(NewStudentPage, owner=request.user, id=page_id).get_latest_revision_as_page()
    data['page_id'] = page_id
    data['is_in_show'] = profile_is_in_show(request, profile_page)
    return data, profile_page


def save_page(page, request):
    """
    """

    submit = False
    if 'submit_for_publication' in request.POST:
        submit = True
        messages.success(request, "Profile page '{}' was submitted for moderation".format(page.title))

    revision = page.save_revision(
        user=request.user,
        submitted_for_moderation=submit,
    )

    page.has_unpublished_changes = True
    page.save()

    return revision


################################################################################
## view functions

@login_required
def overview(request):
    """
    Starting page for student profile editing
    If there already is a student profile page, we simply redirect to editing that one.
    If none exists, we'll create a new one and redirect to that if possible.
    """
    if NewStudentPage.objects.filter(owner=request.user).exists():
        page = NewStudentPage.objects.filter(owner=request.user)[0]
        return redirect('student-profiles:edit-basic', page_id=page.id)

    data = {}
    data['form'] = StartingForm(initial={
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
    })

    if request.method == 'POST':
        data['form'] = form = StartingForm(request.POST)

        if form.is_valid():
            page = NewStudentPage(owner=request.user)
            page.live = False

            page.title = u'{} {}'.format(form.cleaned_data['first_name'], form.cleaned_data['last_name'])

            request.user.first_name = page.first_name = form.cleaned_data['first_name']
            request.user.last_name = page.last_name = form.cleaned_data['last_name']

            # the following is the page where the new student pages are added as children
            # MAKE SURE THIS IS THE CORRECT ID!
            Page.objects.get(id=NEW_STUDENT_PAGE_INDEX_ID).add_child(instance=page)
            # the page slug should not be changed, lest all links go wrong!
            page.slug = slugify(page.title)
            if Page.objects.exclude(id=page.id).filter(slug=page.slug).exists():
                page.slug = '{}-{}'.format(
                    slugify(page.title),
                    page.id,
                )

            page.has_unpublished_changes = True
            page.save()

            request.user.save()

            return redirect('student-profiles:edit-basic', page_id=page.id)

    return render(request, 'student_profiles/overview.html', data)

@login_required
def preview(request, page_id=None):
    """Preview of the profile page."""
    data, profile_page = initial_context(request, page_id)
    
    return profile_page.serve(profile_page.dummy_request())


################################################################################
## basic stuff for everyone

@login_required
def basic_profile(request, page_id):
    """Basic profile creation/editing page"""
    data = {
        'is_ma': user_is_ma(request),
        'is_mphil': user_is_mphil(request),
        'is_phd': user_is_phd(request),
    }

    data['page'] = profile_page = get_object_or_404(NewStudentPage, owner=request.user, id=page_id).get_latest_revision_as_page()
    data['page_id'] = page_id
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

    data['email_formset'].title = 'Email'
    data['phone_formset'].title = 'Phone'
    data['website_formset'].title = 'Website'


    if request.method == 'POST':
        data['basic_form'] = basic_form = ProfileBasicForm(request.POST, request.FILES)
        data['email_formset'] = email_formset = EmailFormset(request.POST, prefix='email')
        data['phone_formset'] = phone_formset = PhoneFormset(request.POST, prefix='phone')
        data['website_formset'] = website_formset = WebsiteFormset(request.POST, prefix='website')

        if profile_page.locked:
            if not request.is_ajax():
                # we don't want to put messages in ajax requests because the user will do a manual post and get the message then
                messages.error(request, 'The page could not saved, it is currently locked')
        elif basic_form.is_valid() and email_formset.is_valid() and phone_formset.is_valid() and website_formset.is_valid():
            bcd = basic_form.cleaned_data
            
            profile_page.title = u'{} {}'.format(bcd['first_name'], bcd['last_name'])

            request.user.first_name = profile_page.first_name = bcd['first_name']
            request.user.last_name = profile_page.last_name = bcd['last_name']

            profile_page.statement = bcd['statement']
            profile_page.twitter_handle = bcd['twitter_handle']

            profile_page.profile_image = bcd['profile_image']

            profile_page.emails = [
                NewStudentPageContactsEmail(email=f['email']) for f in email_formset.ordered_data if f.get('email')
            ]
            profile_page.phones = [
                NewStudentPageContactsPhone(phone=f['phone']) for f in phone_formset.ordered_data if f.get('phone')
            ]
            profile_page.websites = [
                NewStudentPageContactsWebsite(website=f['website']) for f in website_formset.ordered_data if f.get('website')
            ]

            save_page(profile_page, request)
            request.user.save()

            if request.is_ajax():
                return HttpResponse(json.dumps({'ok': True}), content_type='application/json')
            return redirect('student-profiles:edit-basic', page_id=profile_page.id)

    if request.is_ajax():
        return HttpResponse(json.dumps({'ok': False}), content_type='application/json')
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

    make_formset('Experience', ExperiencesFormset, 'experiences', 'experience')

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
        data['experiences_formset'] = xfs = ExperiencesFormset(request.POST, prefix='experiences')
        
        if profile_page.locked:
            if not request.is_ajax():
                # we don't want to put messages in ajax requests because the user will do a manual post and get the message then
                messages.error(request, 'The page could not saved, it is currently locked')
        elif pf.is_valid() and pdfs.is_valid() and efs.is_valid() and pfs.is_valid() and cfs.is_valid() and afs.is_valid() and xfs.is_valid():
            profile_page.funding = pf.cleaned_data['funding']
            
            profile_page.previous_degrees = [
                NewStudentPagePreviousDegree(degree=f['degree']) for f in pdfs.ordered_data if f.get('degree')
            ]
            profile_page.exhibitions = [
                NewStudentPageExhibition(exhibition=f['exhibition']) for f in efs.ordered_data if f.get('exhibition')
            ]
            profile_page.awards = [
                NewStudentPageAward(award=f['award']) for f in afs.ordered_data if f.get('award')
            ]
            profile_page.publications = [
                NewStudentPagePublication(name=f['name']) for f in pfs.ordered_data if f.get('name')
            ]
            profile_page.conferences = [
                NewStudentPageConference(name=f['name']) for f in cfs.ordered_data if f.get('name')
            ]
            profile_page.experiences = [
                NewStudentPageExperience(experience=f['experience']) for f in xfs.ordered_data if f.get('experience')
            ]
            
            save_page(profile_page, request)
        
            if request.is_ajax():
                return HttpResponse(json.dumps({'ok': True}), content_type='application/json')
            return redirect('student-profiles:edit-academic', page_id=profile_page.id)
    
    if request.is_ajax():
        return HttpResponse(json.dumps({'ok': False}), content_type='application/json')
    return render(request, 'student_profiles/academic_details.html', data)


################################################################################
## MA

@login_required
def ma_details(request, page_id):
    if not user_is_ma(request):
        raise Http404("You cannot view MA details because you're not in the MA programme.")
    data, profile_page = initial_context(request, page_id)

    data['ma_form'] = MADetailsForm(instance=profile_page)

    if request.method == 'POST':
        data['ma_form'] = form = MADetailsForm(request.POST, instance=profile_page, )

        if profile_page.locked:
            if not request.is_ajax():
                # we don't want to put messages in ajax requests because the user will do a manual post and get the message then
                messages.error(request, 'The page could not saved, it is currently locked')
        elif form.is_valid():
            page = form.save(commit=False)
            
            save_page(page, request)
            
            if request.is_ajax():
                return HttpResponse(json.dumps({'ok': True}), content_type='application/json')
            return redirect('student-profiles:edit-ma', page_id=page_id)

    if request.is_ajax():
        return HttpResponse(json.dumps({'ok': False}), content_type='application/json')
    return render(request, 'student_profiles/ma_details.html', data)


@login_required
def ma_show_details(request, page_id):
    if not user_is_ma(request):
        raise Http404("You cannot view MA show details because you're not in the MA programme.")

    data, profile_page = initial_context(request, page_id)

    if not profile_is_in_show(request, profile_page):
        messages.warning(request, "You cannot view MA show details because you indicated that you're not in the show this year. If this is not correct, please tick the appropriate box in the detail page.")
        return redirect('student-profiles:edit-ma', page_id=page_id)


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
        
        if profile_page.locked:
            if not request.is_ajax():
                # we don't want to put messages in ajax requests because the user will do a manual post and get the message then
                messages.error(request, 'The page could not saved, it is currently locked')
        elif sf.is_valid() and scif.is_valid() and scf.is_valid() and ssf.is_valid():

            page = sf.save(commit=False)

            carousel_items = [
                {k:v for k,v in f.items() if k not in ('item_type', 'order')}
                for f in scif.ordered_data if f.get('item_type') and (f.get('image_id') or f.get('embedly_url'))
            ]
            page.show_carousel_items = [
                NewStudentPageShowCarouselItem(**item) for item in carousel_items
            ]
            
            page.show_collaborators = [
                NewStudentPageShowCollaborator(name=f['name'].strip()) for f in scf.ordered_data if f.get('name')
            ]
            page.show_sponsors = [
                NewStudentPageShowSponsor(name=f['name'].strip()) for f in ssf.ordered_data if f.get('name')
            ]
            
            save_page(page, request)

            if request.is_ajax():
                return HttpResponse(json.dumps({'ok': True}), content_type='application/json')
            return redirect('student-profiles:edit-ma-show', page_id=page_id)

    if request.is_ajax():
        return HttpResponse(json.dumps({'ok': False}), content_type='application/json')
    return render(request, 'student_profiles/ma_show_details.html', data)


################################################################################
## MPhil and PhD (they're almost the same)

@login_required
def mphil_details(request, page_id):
    if not user_is_mphil(request):
        raise Http404("You cannot view MA show details because you're not in the MA programme.")

    data, profile_page = initial_context(request, page_id)

    data['mphil_form'] = MPhilForm(instance=profile_page)

    carousel_initial = [
        {
            'item_type': 'image' if c.image_id is not None else 'video',
            'image_id': c.image_id, 'overlay_text': c.overlay_text, 'embedly_url': c.embedly_url, 'poster_image_id': c.poster_image_id
        }
        for c in profile_page.mphil_carousel_items.all()
    ]
    data['carouselitem_formset'] = MAShowCarouselItemFormset(prefix='carousel', initial=carousel_initial)

    data['collaborator'] = MPhilCollaboratorFormset(prefix='collaborator', initial=[
        {'name': c.name} for c in profile_page.mphil_collaborators.all()
    ])
    data['sponsor'] = MPhilSponsorFormset(prefix='sponsor', initial=[
        {'name': c.name} for c in profile_page.mphil_sponsors.all()
    ])

    data['collaborator'].title = 'Collaborator'
    data['sponsor'].title = 'Sponsor'

    supervisor_initial = [
        {
            'supervisor_type': 'internal' if s.supervisor is not None else 'other',
            'supervisor': s.supervisor, 'supervisor_other': s.supervisor_other,
        }
        for s in profile_page.mphil_supervisors.all()
    ]
    data['supervisor'] = MPhilSupervisorFormset(prefix='supervisor', initial=supervisor_initial)

    if request.method == 'POST':
        mpf = data['mphil_form'] = MPhilForm(request.POST, instance=profile_page)
        cif = data['carouselitem_formset'] = MAShowCarouselItemFormset(request.POST, prefix='carousel', initial=carousel_initial)
        cof = data['collaborator'] = MPhilCollaboratorFormset(request.POST, prefix='collaborator')
        spf = data['sponsor'] = MPhilSponsorFormset(request.POST, prefix='sponsor')
        suf = data['supervisor'] = MPhilSupervisorFormset(request.POST, prefix='supervisor')

        if profile_page.locked:
            if not request.is_ajax():
                # we don't want to put messages in ajax requests because the user will do a manual post and get the message then
                messages.error(request, 'The page could not saved, it is currently locked')
        elif all(map(lambda f: f.is_valid(), (mpf, cif, cof, spf, suf))):
            
            page = mpf.save(commit=False)
            
            carousel_items = [
                {k:v for k,v in f.items() if k not in ('item_type', 'order')}
                for f in cif.ordered_data if f.get('item_type') and (f.get('image_id') or f.get('embedly_url'))
            ]
            page.mphil_carousel_items = [
                NewStudentPageMPhilCarouselItem(**item) for item in carousel_items
            ]
            
            page.mphil_collaborators = [
                NewStudentPageMPhilCollaborator(name=f['name'].strip()) for f in cof.ordered_data if f.get('name')
            ]
            page.mphil_sponsors = [
                NewStudentPageMPhilSponsor(name=f['name'].strip()) for f in spf.ordered_data if f.get('name')
            ]
            
            page.mphil_supervisors = [
                NewStudentPageMPhilSupervisor(supervisor=c['supervisor'], supervisor_other=c['supervisor_other'])
                for c in suf.ordered_data if c['supervisor'] or c['supervisor_other']
            ]
            
            save_page(page, request)
            
            if request.is_ajax():
                return HttpResponse(json.dumps({'ok': True}), content_type='application/json')
            return redirect('student-profiles:edit-mphil', page_id=page_id)


    if request.is_ajax():
        return HttpResponse(json.dumps({'ok': False}), content_type='application/json')
    return render(request, 'student_profiles/mphil_details.html', data)



@login_required
def phd_details(request, page_id):
    if not user_is_phd(request):
        raise Http404("You cannot view MA show details because you're not in the MA programme.")

    data, profile_page = initial_context(request, page_id)

    data['phd_form'] = PhDForm(instance=profile_page)

    carousel_initial = [
        {
            'item_type': 'image' if c.image_id is not None else 'video',
            'image_id': c.image_id, 'overlay_text': c.overlay_text, 'embedly_url': c.embedly_url, 'poster_image_id': c.poster_image_id
        }
        for c in profile_page.phd_carousel_items.all()
    ]
    data['carouselitem_formset'] = MAShowCarouselItemFormset(prefix='carousel', initial=carousel_initial)

    data['collaborator'] = PhDCollaboratorFormset(prefix='collaborator', initial=[
        {'name': c.name} for c in profile_page.phd_collaborators.all()
    ])
    data['sponsor'] = PhDSponsorFormset(prefix='sponsor', initial=[
        {'name': c.name} for c in profile_page.phd_sponsors.all()
    ])

    data['collaborator'].title = 'Collaborator'
    data['sponsor'].title = 'Sponsor'

    supervisor_initial = [
        {
            'supervisor_type': 'internal' if s.supervisor is not None else 'other',
            'supervisor': s.supervisor, 'supervisor_other': s.supervisor_other,
        }
        for s in profile_page.phd_supervisors.all()
    ]
    data['supervisor'] = PhDSupervisorFormset(prefix='supervisor', initial=supervisor_initial)

    if request.method == 'POST':
        mpf = data['mphil_form'] = PhDForm(request.POST, instance=profile_page)
        cif = data['carouselitem_formset'] = MAShowCarouselItemFormset(request.POST, prefix='carousel', initial=carousel_initial)
        cof = data['collaborator'] = PhDCollaboratorFormset(request.POST, prefix='collaborator')
        spf = data['sponsor'] = PhDSponsorFormset(request.POST, prefix='sponsor')
        suf = data['supervisor'] = PhDSupervisorFormset(request.POST, prefix='supervisor')

        if profile_page.locked:
            if not request.is_ajax():
                # we don't want to put messages in ajax requests because the user will do a manual post and get the message then
                messages.error(request, 'The page could not saved, it is currently locked')
        elif all(map(lambda f: f.is_valid(), (mpf, cif, cof, spf, suf))):
            
            page = mpf.save(commit=False)
            
            carousel_items = [
                {k:v for k,v in f.items() if k not in ('item_type', 'order')}
                for f in cif.ordered_data if f.get('item_type') and (f.get('image_id') or f.get('embedly_url'))
            ]
            page.phd_carousel_items = [
                NewStudentPagePhDCarouselItem(**item) for item in carousel_items
            ]
            
            page.phd_collaborators = [
                NewStudentPagePhDCollaborator(name=f['name'].strip()) for f in cof.ordered_data if f.get('name')
            ]
            page.phd_sponsors = [
                NewStudentPagePhDSponsor(name=f['name'].strip()) for f in spf.ordered_data if f.get('name')
            ]
            
            page.phd_supervisors = [
                NewStudentPagePhDSupervisor(supervisor=c['supervisor'], supervisor_other=c['supervisor_other'])
                for c in suf.ordered_data if c['supervisor'] or c['supervisor_other']
            ]
            
            save_page(page, request)
            
            if request.is_ajax():
                return HttpResponse(json.dumps({'ok': True}), content_type='application/json')
            return redirect('student-profiles:edit-phd', page_id=page_id)


    if request.is_ajax():
        return HttpResponse(json.dumps({'ok': False}), content_type='application/json')
    return render(request, 'student_profiles/phd_details.html', data)




################################################################################
## image handling

@require_POST
@login_required
def image_upload(request, page_id, field=None):
    
    data, profile_page = initial_context(request, page_id)
    
    form = ImageForm(request.POST, request.FILES)
    if profile_page.locked:
        res = {'ok': False, 'errors': 'The page is currently locked and cannot be edited.'}
        return HttpResponse(json.dumps(res), content_type='application/json')
    elif form.is_valid():
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

            profile_page.has_unpublished_changes = True
            profile_page.save()
        
        return HttpResponse('{{"ok": true, "id": {} }}'.format(r.id), content_type='application/json')
    else:
        errors = ', '.join(', '.join(el) for el in form.errors.values())
        res = {'ok': False, 'errors': errors}
        return HttpResponse(json.dumps(res), content_type='application/json')
