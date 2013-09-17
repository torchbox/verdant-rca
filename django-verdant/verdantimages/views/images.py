from django.shortcuts import render

from verdantimages.models import Image

def index(request):
    images = Image.objects.order_by('title')

    return render(request, "verdantimages/images/index.html", {
        'images': images,
    })
