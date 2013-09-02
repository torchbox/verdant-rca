from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType

from core.models import Page, get_page_types


def index(request):
    pages = Page.objects.order_by('title')
    return render(request, 'verdantadmin/pages/index.html', {
        'pages': pages,
    })


def select_type(request):
    # Get the list of page types that can be created within the pages that currently exist
    existing_page_types = ContentType.objects.raw("""
        SELECT DISTINCT content_type_id AS id FROM core_page
    """)

    page_types = set()
    for ct in existing_page_types:
        for subpage_type in ct.model_class().subpage_types:
            page_types.add(ContentType.objects.get_for_model(subpage_type))

    return render(request, 'verdantadmin/pages/select_type.html', {
        'page_types': page_types,
    })


def select_location(request, content_type_app_name, content_type_model_name):
    try:
        content_type = ContentType.objects.get_by_natural_key(content_type_app_name, content_type_model_name)
    except ContentType.DoesNotExist:
        raise Http404
    # content type must be in the list of page types
    if content_type not in get_page_types():
        raise Http404

    page_class = content_type.model_class()
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
    if page_class not in parent_page.subpage_types:
        messages.error(request, "Sorry, you do not have access to create a page of type '%s' here." % content_type.name)
        return redirect('verdantadmin_pages_select_type')

    page = page_class(parent=parent_page)
    form_class = page_class.form_class

    if request.POST:
        form = form_class(request.POST, instance=page)
        if form.is_valid():
            page = form.save()
            messages.success(request, "Page '%s' created." % page.title)
            return redirect('verdantadmin_pages_index')
    else:
        form = form_class(instance=page)

    return render(request, 'verdantadmin/pages/create.html', {
        'content_type': content_type,
        'page_class': page_class,
        'parent_page': parent_page,
        'form': form,
    })


def edit(request, page_id):
    page = get_object_or_404(Page, id=page_id).specific
    form_class = page.form_class

    if request.POST:
        form = form_class(request.POST, instance=page)
        if form.is_valid():
            form.save()
            messages.success(request, "Page '%s' updated." % page.title)
            return redirect('verdantadmin_pages_index')
    else:
        form = form_class(instance=page)

    return render(request, 'verdantadmin/pages/edit.html', {
        'page': page,
        'form': form,
    })
