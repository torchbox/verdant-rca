from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from verdant.verdantadmin.edit_handlers import ObjectList

from verdant.verdantredirects import models


REDIRECT_EDIT_HANDLER = ObjectList(models.Redirect.content_panels)

@login_required
def index(request):
    print request.get_full_path()
    # Get redirects
    redirects = models.Redirect.get_for_site(site=request.site)

    # Render template
    return render(request, "verdantredirects/index.html", {
        'redirects': redirects,
    })


@login_required
def edit(request, redirect_id):
    theredirect = get_object_or_404(models.Redirect, id=redirect_id)

    form_class = REDIRECT_EDIT_HANDLER.get_form_class(models.Redirect)
    if request.POST:
        form = form_class(request.POST, request.FILES, instance=theredirect)
        if form.is_valid():
            form.save()
            messages.success(request, "Redirect '%s' updated." % theredirect.title)
            return redirect('verdantredirects_index')
        else:
            messages.error(request, "The redirect could not be saved due to validation errors")
            edit_handler = REDIRECT_EDIT_HANDLER(instance=theredirect, form=form)
    else:
        form = form_class(instance=theredirect)
        edit_handler = REDIRECT_EDIT_HANDLER(instance=theredirect, form=form)

    return render(request, "verdantredirects/edit.html", {
        'redirect': theredirect,
        'edit_handler': edit_handler,
    })


@login_required
def delete(request, redirect_id):
    theredirect = get_object_or_404(models.Redirect, id=redirect_id)

    if request.POST:
        theredirect.delete()
        messages.success(request, "Redirect '%s' deleted." % theredirect.title)
        return redirect('verdantredirects_index')

    return render(request, "verdantredirects/confirm_delete.html", {
        'redirect': theredirect,
    })


@login_required
def add(request):
    theredirect = models.Redirect()

    form_class = REDIRECT_EDIT_HANDLER.get_form_class(models.Redirect)
    if request.POST:
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            theredirect = form.save(commit=False)
            theredirect.site = request.site
            theredirect.save()

            messages.success(request, "Redirect '%s' added." % theredirect.title)
            return redirect('verdantredirects_index')
        else:
            messages.error(request, "The redirect could not be created due to validation errors")
            edit_handler = REDIRECT_EDIT_HANDLER(instance=theredirect, form=form)
    else:
        form = form_class()
        edit_handler = REDIRECT_EDIT_HANDLER(instance=theredirect, form=form)

    return render(request, "verdantredirects/add.html", {
        'edit_handler': edit_handler,
    })