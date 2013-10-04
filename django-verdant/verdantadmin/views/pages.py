from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType

from treebeard.exceptions import InvalidMoveToDescendant

from core.models import Page, get_page_types
from verdantadmin.edit_handlers import TabbedInterface, ObjectList

def index(request, parent_page_id=None):

    if parent_page_id:
        parent_page = get_object_or_404(Page, id=parent_page_id)
    else:
        parent_page = Page.get_first_root_node()

    pages = parent_page.get_children().order_by('title')
    return render(request, 'verdantadmin/pages/index.html', {
        'parent_page': parent_page,
        'pages': pages,
    })


def select_type(request):
    # Get the list of page types that can be created within the pages that currently exist
    existing_page_types = ContentType.objects.raw("""
        SELECT DISTINCT content_type_id AS id FROM core_page
    """)

    page_types = set()
    for ct in existing_page_types:
        allowed_subpage_types = ct.model_class().clean_subpage_types()
        for subpage_type in allowed_subpage_types:
            subpage_content_type = ContentType.objects.get_for_model(subpage_type)

            page_types.add(subpage_content_type)

    return render(request, 'verdantadmin/pages/select_type.html', {
        'page_types': page_types,
    })


def add_subpage(request, parent_page_id):
    parent_page = get_object_or_404(Page, id=parent_page_id).specific

    page_types = sorted([ContentType.objects.get_for_model(model_class) for model_class in parent_page.clean_subpage_types()], key=lambda pagetype: pagetype.name)
    all_page_types = sorted(get_page_types(), key=lambda pagetype: pagetype.name)

    return render(request, 'verdantadmin/pages/add_subpage.html', {
        'parent_page': parent_page,
        'page_types': page_types,
        'all_page_types': all_page_types,
    })

def select_location(request, content_type_app_name, content_type_model_name):
    try:
        content_type = ContentType.objects.get_by_natural_key(content_type_app_name, content_type_model_name)
    except ContentType.DoesNotExist:
        raise Http404

    page_class = content_type.model_class()
    # page_class must be a Page type and not some other random model
    if not issubclass(page_class, Page):
        raise Http404

    # find all the valid locations (parent pages) where a page of the chosen type can be added
    parent_pages = page_class.allowed_parent_pages()

    if len(parent_pages) == 0:
        # user cannot create a page of this type anywhere - fail with an error
        messages.error(request, "Sorry, you do not have access to create a page of type '%s'." % content_type.name)
        return redirect('verdantadmin_pages_select_type')
    elif len(parent_pages) == 1:
        # only one possible location - redirect them straight there
        return redirect('verdantadmin_pages_create', content_type_app_name, content_type_model_name, parent_pages[0].id)
    else:
        # prompt them to select a location
        return render(request, 'verdantadmin/pages/select_location.html', {
            'content_type': content_type,
            'page_class': page_class,
            'parent_pages': parent_pages,
        })


def create(request, content_type_app_name, content_type_model_name, parent_page_id):
    parent_page = get_object_or_404(Page, id=parent_page_id).specific

    try:
        content_type = ContentType.objects.get_by_natural_key(content_type_app_name, content_type_model_name)
    except ContentType.DoesNotExist:
        raise Http404

    page_class = content_type.model_class()

    # page must be in the list of allowed subpage types for this parent ID
    # == Restriction temporarily relaxed so that as superusers we can add index pages and things -
    # == TODO: reinstate this for regular editors when we have distinct user types
    #
    # if page_class not in parent_page.clean_subpage_types():
    #     messages.error(request, "Sorry, you do not have access to create a page of type '%s' here." % content_type.name)
    #     return redirect('verdantadmin_pages_select_type')

    page = page_class()
    edit_handler_class = get_page_edit_handler(page_class)
    form_class = edit_handler_class.get_form_class(page_class)

    if request.POST:
        form = form_class(request.POST, request.FILES, instance=page)
        edit_handler = edit_handler_class(request.POST, request.FILES, instance=page, form=form)

        if all([form.is_valid(), edit_handler.is_valid()]):
            edit_handler.pre_save()
            page = form.save(commit=False)  # don't save yet, as we need treebeard to assign tree params
            parent_page.add_child(page)  # assign tree parameters - will cause page to be saved
            edit_handler.post_save()  # perform the steps we couldn't save without a db model (e.g. saving inline relations)

            messages.success(request, "Page '%s' created." % page.title)
            return redirect('verdantadmin_explore', page.get_parent().id)
    else:
        form = form_class(instance=page)
        edit_handler = edit_handler_class(instance=page, form=form)

    return render(request, 'verdantadmin/pages/create.html', {
        'content_type': content_type,
        'page_class': page_class,
        'parent_page': parent_page,
        'edit_handler': edit_handler,
    })


def edit(request, page_id):
    page = get_object_or_404(Page, id=page_id).specific
    edit_handler_class = get_page_edit_handler(page.__class__)
    form_class = edit_handler_class.get_form_class(page.__class__)

    if request.POST:
        form = form_class(request.POST, request.FILES, instance=page)
        edit_handler = edit_handler_class(request.POST, request.FILES, instance=page, form=form)

        if all([form.is_valid(), edit_handler.is_valid()]):
            edit_handler.pre_save()
            form.save()
            edit_handler.post_save()
            messages.success(request, "Page '%s' updated." % page.title)
            return redirect('verdantadmin_explore', page.get_parent().id)
    else:
        form = form_class(instance=page)
        edit_handler = edit_handler_class(instance=page, form=form)

    return render(request, 'verdantadmin/pages/edit.html', {
        'page': page,
        'edit_handler': edit_handler,
    })

def delete(request, page_id):
    page = get_object_or_404(Page, id=page_id)

    if request.POST:
        parent_id = page.get_parent().id
        page.delete()
        messages.success(request, "Page '%s' deleted." % page.title)
        return redirect('verdantadmin_explore', parent_id)

    return render(request, 'verdantadmin/pages/confirm_delete.html', {
        'page': page,
        'descendant_count': page.get_descendant_count()
    })

def move_choose_destination(request, page_to_move_id, viewed_page_id=None):
    page_to_move = get_object_or_404(Page, id=page_to_move_id)

    if viewed_page_id:
        viewed_page = get_object_or_404(Page, id=viewed_page_id)
    else:
        viewed_page = Page.get_first_root_node()

    child_pages = []
    for page in viewed_page.get_children():
        # can't move the page into itself or its descendants
        can_choose = not(page == page_to_move or page.is_child_of(page_to_move))

        can_descend = can_choose and page.get_children_count()

        child_pages.append({
            'page': page, 'can_choose': can_choose, 'can_descend': can_descend,
        })

    return render(request, 'verdantadmin/pages/move_choose_destination.html', {
        'page_to_move': page_to_move,
        'viewed_page': viewed_page,
        'child_pages': child_pages,
    })

def move_confirm(request, page_to_move_id, destination_id):
    page_to_move = get_object_or_404(Page, id=page_to_move_id)
    destination = get_object_or_404(Page, id=destination_id)

    if request.POST:
        try:
            page_to_move.move(destination, pos='last-child')

            messages.success(request, "Page '%s' moved." % page_to_move.title)
            return redirect('verdantadmin_explore', destination.id)
        except InvalidMoveToDescendant:
            messages.error(request, "You cannot move this page into itself.")
            return redirect('verdantadmin_pages_move', page_to_move.id)

    else:
        if page_to_move == destination or destination.is_descendant_of(page_to_move):
            messages.error(request, "You cannot move this page into itself.")
            return redirect('verdantadmin_pages_move', page_to_move.id)

    return render(request, 'verdantadmin/pages/confirm_move.html', {
        'page_to_move': page_to_move,
        'destination': destination,
    })


PAGE_EDIT_HANDLERS = {}
def get_page_edit_handler(page_class):
    if page_class not in PAGE_EDIT_HANDLERS:
        PAGE_EDIT_HANDLERS[page_class] = TabbedInterface([
            ObjectList(page_class.content_panels, heading='Content'),
            ObjectList(page_class.promote_panels, heading='Promote')
        ])

    return PAGE_EDIT_HANDLERS[page_class]
