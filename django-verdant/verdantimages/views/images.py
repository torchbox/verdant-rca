from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from verdantimages.models import Image
from verdantimages.forms import ImageForm, EditImageForm, ImageSearchForm
from taggit.models import Tag

def index(request):
    images = Image.objects.order_by('title')

    return render(request, "verdantimages/images/index.html", {
        'images': images,
    })


def edit(request, image_id):
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
    image = get_object_or_404(Image, id=image_id)

    if request.POST:
        image.delete()
        messages.success(request, "Image '%s' deleted." % image.title)
        return redirect('verdantimages_index')

    return render(request, "verdantimages/images/confirm_delete.html", {
        'image': image,
    })


def add(request):
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
    images = Image.objects.order_by('title')
    tags = Tag.objects.none()
    tag_matches = None
    title_matches = Image.objects.none()
    if 'q' in request.GET:
        form = ImageSearchForm(request.GET)
        if form.is_valid():
            strings = form.cleaned_data['q'].split()
            for string in strings:
                tags = tags | Tag.objects.filter(name__istartswith=string)
            # NB the following line will select images if any tags match, not just if all do
            tag_matches = images.filter(tags__in = tags).distinct()
            for term in strings:
                title_matches = title_matches | images.filter(title__istartswith=term).distinct()
            images = tag_matches | title_matches
    else:
        form = ImageSearchForm()

    context = {
        'form': form,
        'images': images,
        'tags': tags,
    }
    if request.is_ajax():
        return render(request, "verdantimages/images/search-results.html", context)
    else:
        return render(request, "verdantimages/images/search.html", context)
