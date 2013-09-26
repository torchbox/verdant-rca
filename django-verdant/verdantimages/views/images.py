from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from verdantimages.models import get_image_model
from verdantimages.forms import get_image_form
from verdantadmin.forms import SearchForm

def index(request):
    Image = get_image_model()
    images = Image.objects.order_by('-created_at')[:12]
    form = SearchForm()

    return render(request, "verdantimages/images/index.html", {
        'images': images,
        'form': form,
        'popular_tags': Image.popular_tags(),
        'is_searching': False,
    })


def edit(request, image_id):
    Image = get_image_model()
    ImageForm = get_image_form()

    image = get_object_or_404(Image, id=image_id)

    if request.POST:
        original_file = image.file
        form = ImageForm(request.POST, request.FILES, instance=image)
        if form.is_valid():
            if 'file' in form.changed_data:
                # if providing a new image file, delete the old one and all renditions.
                # NB Doing this via original_file.delete() clears the file field,
                # which definitely isn't what we want...
                original_file.storage.delete(original_file.name)
                image.renditions.all().delete()
            form.save()
            messages.success(request, "Image '%s' updated." % image.title)
            return redirect('verdantimages_index')

    else:
        form = ImageForm(instance=image)

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
    Image = get_image_model()
    images = []
    if 'q' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            q = form.cleaned_data['q']
            images = Image.search(q)
    else:
        form = SearchForm()

    if request.is_ajax():
        return render(request, "verdantimages/images/search-results.html", {
            'images': images,
        })
    else:
        return render(request, "verdantimages/images/index.html", {
            'form': form,
            'images': images,
            'is_searching': True,
            'popular_tags': Image.popular_tags(),
        })
