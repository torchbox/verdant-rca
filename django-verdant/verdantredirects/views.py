from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required

import models
import forms


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

    if request.POST:
        form = forms.RedirectForm(request.POST, request.FILES, instance=theredirect)
        if form.is_valid():
            form.save()
            messages.success(request, "Redirect '%s' updated." % theredirect.title)
            return redirect('verdantredirects_index')

    else:
        form = forms.RedirectForm(instance=theredirect)

    return render(request, "verdantredirects/edit.html", {
        'redirect': theredirect,
        'form': form,
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
    if request.POST:
        form = forms.RedirectForm(request.POST, request.FILES)
        if form.is_valid():
            theredirect = form.save()
            messages.success(request, "Redirect '%s' added." % theredirect.title)
            return redirect('verdantredirects_index')
    else:
        form = forms.RedirectForm()

    return render(request, "verdantredirects/add.html", {
        'form': form,
    })