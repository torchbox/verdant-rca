# RCA-specific extensions to Verdant admin.

import requests

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render, redirect

from wagtail.wagtailadmin import messages
from wagtail.wagtailcore.models import Page, UserPagePermissionsProxy

from rca.models import RcaNowPage, RcaNowIndex, NewStudentPage, StandardIndex

def find_rca_now_index_page(user):
    """Look for the RCA Now index page: a page of type RcaNowIndex where this user can add pages"""
    user_perms = UserPagePermissionsProxy(user)

    for page in RcaNowIndex.objects.all():
        if user_perms.for_page(page).can_add_subpage():
            return page

    raise Exception('No usable RCA Now section found (using the RcaNowIndex page type and with add permission for students)')

def find_student_index_page(user):
    """Look for the student index page: a page of type StandardIndex with slug "students" where this user can add pages"""
    user_perms = UserPagePermissionsProxy(user)

    for page in StandardIndex.objects.filter(slug='students'):
        if user_perms.for_page(page).can_add_subpage():
            return page

    raise Exception('No usable student index found (using the StandardIndex page type and with add permission for students)')

@login_required
def rca_now_index(request):
    index_page = find_rca_now_index_page(request.user)

    pages = RcaNowPage.objects.filter(owner=request.user)
    return render(request, 'rca/admin/rca_now_index.html', {
        'rca_now_index': index_page,
        'hide_actions': ('move', 'add_subpage'),
        'pages': pages,
    })

@login_required
def student_page_index(request):
    # look for StudentPages owned by this user
    pages = NewStudentPage.objects.filter(owner=request.user)

    if not pages:
        index_page = find_student_index_page(request.user)

        # Redirect to the interface for adding a StudentPage in this section
        return redirect('wagtailadmin_pages_create', 'rca', 'newstudentpage', index_page.id)

    elif len(pages) == 1:
        # redirect them to edit their existing student page
        return redirect('wagtailadmin_pages_edit', pages[0].id)

    else:
        return render(request, 'rca/admin/select_student_page.html', {
            'pages': pages,
            'hide_actions': ('move', 'add_subpage'),
        })


def push_to_intranet(request, page_id):
    # Get page
    page = get_object_or_404(Page, id=page_id)

    # User must have publish permission
    user_perms = UserPagePermissionsProxy(request.user)
    page_perms = user_perms.for_page(page)
    if not page_perms.can_publish():
        raise PermissionDenied

    if request.method == "POST":
        # Perform request
        url = settings.INTRANET_PUSH_URL.format(
            type=page._meta.app_label + '.' + page.__class__.__name__,
            id=page.id,
        )
        response = requests.post(url)

        if response.status_code == 200:
            intranet_url = response.json()['public_url']

            # Success message
            message = "Successfully pushed '{0}' to the intranet.".format(page.title)
            messages.success(request, message, buttons=[
                messages.button(
                    intranet_url,
                    'View on intranet'
                ),
            ])
        else:
            # Error message
            message = "Error received while pushing '{0}' to the intranet. (status code: {1})".format(page.title, response.status_code)
            messages.error(request, message)

        return redirect('wagtailadmin_explore', page.get_parent().id)

    return render(request, 'rca/admin/push_to_intranet.html', {
        'page': page,
    })
