
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
from rca.models import RcaNowPage
from rca.models import RcaImage

from .now_forms import PageForm
from .views import slugify


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
    return get_object_or_404(index_page.get_children(), owner=request.user, id=page_id).get_latest_revision_as_page()


################################################################################
## view functions

@login_required
def overview(request):
    """
    Profile overview page, shows all pages that this user created.
    """
    data = {}

    index_page = Page.objects.get(id=RCA_NOW_INDEX_ID)
    raw_pages = index_page.get_children().filter(owner=request.user)
    data['pages'] = [p.get_latest_revision_as_page() for p in raw_pages]
    for p in data['pages']:
        p.waiting_for_moderation = p.revisions.filter(submitted_for_moderation=True).exists()

    return render(request, 'student_profiles/now_overview.html', data)


@login_required
def edit(request, page_id=None):
    if page_id is not None:
        page = get_page_or_404(request, page_id)
    else:
        page = RcaNowPage(owner=request.user)
    data = {
        'page': page,
    }
    
    data['form'] = PageForm(instance=page)
    
    if request.method == 'POST':
        data['form'] = form = PageForm(request.POST, instance=page)

        if page.locked:
            if not request.is_ajax():
                messages.error(request, 'The page could not be saved, it is currently locked.')
                # fall through to regular rendering
        elif form.is_valid():
            page = form.save(commit=False)
            submit_for_moderation = 'submit_for_moderation' in request.POST
            
            page.tags = [
                Tag.objects.get_or_create(name=tagname)[0] for tagname in form.cleaned_data['tags']
            ]
            
            print page.tags
            print form.cleaned_data
            
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

            page.has_unpublished_changes = True
            page.save()

            if submit_for_moderation:
                return redirect('nowpages:overview')
            elif request.is_ajax():
                return HttpResponse(json.dumps({'ok': True}), content_type='application/json')
            else:
                return redirect('nowpages:edit', page_id=page.id)

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

    messages.success(request, "Blog page '{}' was submitted for moderation".format(page.title))

    return redirect('nowpages:overview')
