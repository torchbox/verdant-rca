from django.shortcuts import render, redirect, get_object_or_404

from django.contrib import messages

from core.models import Page


def index(request):
    pages = Page.objects.order_by('title')
    return render(request, 'verdantadmin/pages/index.html', {
        'pages': pages,
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
