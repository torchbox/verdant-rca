from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404

import json

from verdantimages.models import Image

def chooser(request):
    images = Image.objects.order_by('title')

    html = render_to_string('verdantimages/chooser/chooser.html', {'images': images})
    js = render_to_string('verdantimages/chooser/chooser.js', {'images': images})

    return HttpResponse("""
        {
            'html': %s,
            'onload': %s
        }
    """ % (json.dumps(html), js), mimetype="text/javascript")


def image_chosen(request, image_id):
    image = get_object_or_404(Image, id=image_id)

    preview_image = image.get_in_format('130x100')

    image_json = json.dumps({
        'id': image.id,
        'title': image.title,
        'preview': {
            'url': preview_image.url,
            'width': preview_image.width,
            'height': preview_image.height,
        }
    })

    js = render_to_string('verdantimages/chooser/image_chosen.js', {'image_json': image_json})

    return HttpResponse("""
        {
            'onload': %s
        }
    """ % js, mimetype="text/javascript")
