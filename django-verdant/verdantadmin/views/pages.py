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


def create(request, content_type_id):
    try:
        content_type = ContentType.objects.get_for_id(content_type_id)
    except ContentType.DoesNotExist:
        raise Http404

    # content type must be in the list of page types
    if content_type not in get_page_types():
        raise Http404

    page_class = content_type.model_class()
    form_class = page_class.form_class

    if request.POST:
        form = form_class(request.POST)
        if form.is_valid():
            page = form.save()
            messages.success(request, "Page '%s' created." % page.title)
            return redirect('verdantadmin_pages_index')
    else:
        form = form_class()

    return render(request, 'verdantadmin/pages/create.html', {
        'content_type': content_type,
        'page_class': page_class,
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
