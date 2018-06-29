from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.menu import MenuItem
from wagtail.wagtailadmin import widgets as wagtailadmin_widgets

from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls import url
from django.templatetags.static import static
from django.utils.html import format_html

from .models import RcaNowPage
from . import admin_views


def editor_css():
    return """<link rel="stylesheet" type="text/x-scss" href="%srca/css/richtext.scss" />""" % settings.STATIC_URL
hooks.register('insert_editor_css', editor_css)


def user_is_student(user):
    return [group.name for group in user.groups.all()] == ['Students']


def construct_main_menu(request, menu_items):
    if user_is_student(request.user):
        # remove Explorer and Search items from the menu.
        # assigning menu_items[:] will modify the list passed in
        menu_items[:] = [item for item in menu_items if item.name not in ('explorer', 'search')]

        # insert student page and RCA Now items in place
        menu_items.append(
            MenuItem('Profile', reverse('student_page_editor_index'), classnames='icon icon-user', order=100)
        )
        menu_items.append(
            MenuItem('Posts', reverse('rca_now_editor_index'), classnames='icon icon-doc-full-inverse', order=101)
        )
hooks.register('construct_main_menu', construct_main_menu)


def redirect_student_after_edit(request, page):
    if user_is_student(request.user):
        # Override the usual redirect to the explorer that happens after adding / deleting / editing a page;
        # instead, take them to the homepage or the RCA Now index, according to the type of the page just edited.
        if page.content_type == ContentType.objects.get_for_model(RcaNowPage):
            return redirect('rca_now_editor_index')
        else:
            return redirect('wagtailadmin_home')
hooks.register('after_create_page', redirect_student_after_edit)
hooks.register('after_edit_page', redirect_student_after_edit)
hooks.register('after_delete_page', redirect_student_after_edit)


def construct_homepage_panels(request, panels):
    if user_is_student(request.user):
        # remove site_summary panel.
        # assigning panels[:] will modify the list passed in
        panels[:] = [p for p in panels if p.name != 'site_summary']
hooks.register('construct_homepage_panels', construct_homepage_panels)


@hooks.register('register_page_listing_buttons')
def page_listing_buttons(page, page_perms, is_parent=False):
    if not getattr(settings, 'INTRANET_PUSH_URL', False):
        return

    if page.live and page_perms.can_publish() and getattr(page, 'pushable_to_intranet', False):
        yield wagtailadmin_widgets.PageListingButton(
            'Push to intranet',
            reverse('push_to_intranet', args=(page.id, )),
            priority=40
        )


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^push_to_intranet/(\d+)/$', admin_views.push_to_intranet, name='push_to_intranet'),
    ]

@hooks.register('insert_editor_js')
def add_staff_page_admin_editor_javascript():
    return format_html('<script src="{}"></script>'.format(
        static('rca/js/staff-page-editor.js')
    ))
