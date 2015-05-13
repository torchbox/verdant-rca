
import re
import unicodedata
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from taggit.models import Tag

from wagtail.wagtailcore.models import Page
from rca.models import RcaNowPage, NewStudentPage
from rca.models import RcaImage, RcaNowPagePageCarouselItem, RcaNowPageRelatedLink, RcaNowPageArea

from .now_forms import PageForm, RelatedLinkFormset, AreaFormSet
from .views import slugify, user_is_ma, user_is_mphil, user_is_phd, profile_is_in_show, make_carousel_initial, \
    make_carousel_items, SHOW_PAGES_ENABLED
from .forms import MAShowCarouselItemFormset, ImageForm


# this is the ID of the page where new student pages are added as children
# MAKE SURE IT IS CORRECT FOR YOUR INSTANCE!
RCA_NOW_INDEX_ID = 36


################################################################################
## helper functions

def get_page_or_404(request, page_id):
    """
    Get the page with the given id if it belongs to the user in the request, otherwise throw a 404.
    """
    index_page = Page.objects.get(id=RCA_NOW_INDEX_ID)
    child_page = get_object_or_404(index_page.get_children(), owner=request.user, id=page_id).get_latest_revision_as_page()
    if not isinstance(child_page, RcaNowPage):
        raise Http404("Page of correct type could not be found")
    return child_page


def initial_data(request, page_id=None):
    """
    Create initial data for all requests, so that navigation and stuff works correctly.
    """
    data = {
        'is_ma': user_is_ma(request),
        'is_mphil': user_is_mphil(request),
        'is_phd': user_is_phd(request),
    }

    if NewStudentPage.objects.filter(owner=request.user).exists():
        profile_page = NewStudentPage.objects.filter(owner=request.user)[0]
        data['page_id'] = profile_page.id
        data['is_in_show'] = profile_is_in_show(request, profile_page)
        data['profile_name'] = profile_page.title
        data['SHOW_PAGES_ENABLED'] = SHOW_PAGES_ENABLED

    if page_id is not None:
        page = get_page_or_404(request, page_id)
        data['page'] = page

    return data


################################################################################
## view functions

@login_required
def overview(request):
    """
    Profile overview page, shows all pages that this user created.
    """
    data = initial_data(request)
    data['nav_now'] = True

    index_page = Page.objects.get(id=RCA_NOW_INDEX_ID)
    raw_pages = index_page.get_children().filter(owner=request.user).order_by('-latest_revision_created_at')
    data['pages'] = [p.get_latest_revision_as_page() for p in raw_pages if isinstance(p, RcaNowPage)]
    for p in data['pages']:
        p.waiting_for_moderation = p.revisions.filter(submitted_for_moderation=True).exists()

    return render(request, 'student_profiles/now_overview.html', data)


@login_required
def edit(request, page_id=None):
    data = initial_data(request, page_id)
    if page_id is None:
        page = RcaNowPage(owner=request.user)
    else:
        page = data['page']

    data['nav_now'] = True
    data['form'] = PageForm(instance=page)
    data['link_formset'] = RelatedLinkFormset(
        prefix='links',
        initial=[{'link': x.link} for x in page.related_links.all()]
    )
    data['area_formset'] = AreaFormSet(
        prefix='area',
        initial=[{'area': x.area} for x in page.areas.all()],
    )

    carousel_initial = make_carousel_initial(page.carousel_items.all())
    data['carouselitem_formset'] = MAShowCarouselItemFormset(prefix='carousel', initial=carousel_initial)

    if request.method == 'POST':
        data['form'] = form = PageForm(request.POST, instance=page)
        data['link_formset'] = lif = RelatedLinkFormset(request.POST, prefix='links')
        data['area_formset'] = aef = AreaFormSet(request.POST, prefix='area')
        data['carouselitem_formset'] = cif = MAShowCarouselItemFormset(request.POST, request.FILES, prefix='carousel', initial=carousel_initial)

        if page.locked:
            if not request.is_ajax():
                messages.error(request, 'The page could not be saved, it is currently locked.')
                # fall through to regular rendering
        elif all((form.is_valid(), cif.is_valid(), lif.is_valid(), aef.is_valid())):
            page = form.save(commit=False)
            submit_for_moderation = 'submit_for_moderation' in request.POST

            page.tags.clear()
            for tag in [Tag.objects.get_or_create(name=tagname)[0] for tagname in form.cleaned_data['tags']]:
                page.tags.add(tag)

            page.related_links = [
                RcaNowPageRelatedLink(link=f['link']) for f in lif.ordered_data if f.get('link')
            ]
            page.areas = [
                RcaNowPageArea(area=f['area']) for f in aef.ordered_data if f.get('area')
            ]
            page.carousel_items = make_carousel_items(cif.ordered_data, RcaNowPagePageCarouselItem)

            if page_id is None:
                page.live = False
                page.show_on_homepage = False
                Page.objects.get(id=RCA_NOW_INDEX_ID).add_child(instance=page)
                page.slug = slugify(page.title)
                if Page.objects.exclude(id=page.id).filter(slug=page.slug).exists():
                    page.slug = '{}-{}'.format(
                        slugify(page.title),
                        page.id,
                    )
            
            revision = page.save_revision(
                user=request.user,
                submitted_for_moderation=submit_for_moderation
            )

            page.locked = page.locked or submit_for_moderation
            page.has_unpublished_changes = True
            page.save()

            if submit_for_moderation:
                return redirect('nowpages:overview')
            elif request.is_ajax():
                return HttpResponse(json.dumps({'ok': True}), content_type='application/json')
            else:
                if 'preview' in request.POST:
                    return redirect('nowpages:preview', page_id=page.id)
                return redirect('nowpages:edit', page_id=page.id)
        else:
            e = []
            if not form.is_valid(): e.append('your post content and fields')
            if not cif.is_valid(): e.append('the carousel items')
            if not aef.is_valid(): e.append('the post area')
            if not lif.is_valid(): e.append('your website links')
            data['errors'] = ' and '.join(e)

    if request.is_ajax():
        return HttpResponse(json.dumps({'ok': False}), content_type='application/json')
    return render(request, 'student_profiles/now_edit.html', data)


@login_required
def preview(request, page_id):
    page = get_page_or_404(request, page_id)
    return page.serve(page.dummy_request())


@require_POST
@login_required
def submit(request, page_id):
    page = get_page_or_404(request, page_id)

    page.save_revision(
        user=request.user,
        submitted_for_moderation=True,
    )
    page.locked = True
    page.save()

    messages.success(request, u"Blog page '{}' was submitted for moderation".format(page.title))

    return redirect('nowpages:overview')


@login_required()
def delete(request, page_id):
    page = get_page_or_404(request, page_id)

    if page.live:
        raise Http404('Can only delete pages that are not yet live.')

    if request.method == 'POST':
        Page.objects.get(id=page_id).delete()
        return redirect('nowpages:overview')

    data = {
        'page': page,
        'page_id': page_id,
    }

    return render(request, 'student_profiles/now_delete.html', data)



@require_POST
@login_required
def image_upload(request, page_id, max_size=None, min_dim=None):
    """Upload an image file and create an RcaImage out of it. Specific for NowPages

    If max_size or min_dim (2-tuple) are given, filesize and image dimensions are checked.
    """

    page = get_page_or_404(request, page_id)

    form = ImageForm(request.POST, request.FILES, max_size=max_size, min_dim=min_dim)
    if page.locked:
        res = {'ok': False, 'errors': 'The page is currently locked and cannot be edited.'}
        return HttpResponse(json.dumps(res), content_type='application/json')
    elif form.is_valid():
        r = RcaImage.objects.create(
            file=form.cleaned_data['image'],
            uploaded_by_user=request.user,
        )

        return HttpResponse('{{"ok": true, "id": {} }}'.format(r.id), content_type='application/json')
    else:
        errors = ', '.join(', '.join(el) for el in form.errors.values())
        res = {'ok': False, 'errors': errors}
        return HttpResponse(json.dumps(res), content_type='application/json')