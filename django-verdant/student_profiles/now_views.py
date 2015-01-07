
import re
import unicodedata
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from wagtail.wagtailcore.models import Page
from rca.models import RcaNowPage
from rca.models import RcaImage


from .forms import ImageForm


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
def create(request):
    pass


@login_required
def edit(request, page_id):
    pass


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
