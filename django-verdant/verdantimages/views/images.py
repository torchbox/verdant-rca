from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from verdantimages.models import Image
from verdantimages.forms import EditImageForm

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
