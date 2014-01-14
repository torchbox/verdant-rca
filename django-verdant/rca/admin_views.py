# RCA-specific extensions to Verdant admin.

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from core.models import Page, UserPagePermissionsProxy

from rca.models import RcaNowPage, RcaNowIndex, StudentPage

@login_required
def rca_now_index(request):
    # Look for the RCA Now index: a page of type RcaNowIndex where this user can add pages
    user_perms = UserPagePermissionsProxy(request.user)

    index_page = None
    for page in RcaNowIndex.objects.all():
        if user_perms.for_page(page).can_add_subpage():
            index_page = page
            break

    if not index_page:
        raise Exception('No usable RCA Now section found (using the RcaNowIndex page type and with add permission for students)')

    pages = RcaNowPage.objects.filter(owner=request.user)
    return render(request, 'rca/admin/rca_now_index.html', {
        'rca_now_index': index_page,
        'pages': pages,
    })

@login_required
def student_page_index(request):
    # look for StudentPages owned by this user
    pages = StudentPage.objects.filter(owner=request.user)

    if not pages:
        # look for the Show RCA index: a page with slug 'show-rca' where this user can add pages
        user_perms = UserPagePermissionsProxy(request.user)

        index_page = None
        for page in Page.objects.filter(slug='show-rca'):
            if user_perms.for_page(page).can_add_subpage():
                index_page = page
                break

        if not index_page:
            raise Exception('No usable Show RCA section found (with slug show-rca and add permission for students)')

        # Redirect to the interface for adding a StudentPage in this section
        return redirect('verdantadmin_pages_create', 'rca', 'studentpage', index_page.id)

    elif len(pages) == 1:
        # redirect them to edit their existing student page
        return redirect('verdantadmin_pages_edit', pages[0].id)

    else:
        return render(request, 'rca/admin/select_student_page.html', {
            'pages': pages,
        })
