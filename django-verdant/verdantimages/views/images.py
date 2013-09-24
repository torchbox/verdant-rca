from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from verdantimages.models import get_image_model
from verdantimages.forms import get_image_form, get_edit_image_form
from verdantadmin.forms import SearchForm

def index(request):
    images = get_image_model().objects.order_by('title')

    return render(request, "verdantimages/images/index.html", {
        'images': images,
    })


def edit(request, image_id):
    Image = get_image_model()
    EditImageForm = get_edit_image_form()

    image = get_object_or_404(Image, id=image_id)

    if request.POST:
        form = EditImageForm(request.POST, instance=image)
        if form.is_valid():
            form.save()
            messages.success(request, "Image '%s' updated." % image.title)
            return redirect('verdantimages_index')

    else:
        form = EditImageForm(instance=image)

    return render(request, "verdantimages/images/edit.html", {
        'image': image,
        'form': form,
    })


def delete(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    if request.POST:
        image.delete()
        messages.success(request, "Image '%s' deleted." % image.title)
        return redirect('verdantimages_index')

    return render(request, "verdantimages/images/confirm_delete.html", {
        'image': image,
    })


def add(request):
    ImageForm = get_image_form()

    if request.POST:
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save()
            messages.success(request, "Image '%s' added." % image.title)
            return redirect('verdantimages_index')

    else:
        form = ImageForm()

    return render(request, "verdantimages/images/add.html", {
        'form': form,
    })


def search(request):
    images = []
    if 'q' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            q = form.cleaned_data['q']
            images = get_image_model().search(q)
    else:
        form = SearchForm()

    context = {
        'form': form,
        'images': images,
    }
    if request.is_ajax():
        return render(request, "verdantimages/images/search-results.html", context)
    else:
        return render(request, "verdantimages/images/search.html", context)
