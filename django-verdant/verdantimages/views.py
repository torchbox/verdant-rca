from django.shortcuts import get_object_or_404

import json

from verdantadmin.modal_workflow import render_modal_workflow
from verdantimages.models import Image

def chooser(request):
    images = Image.objects.order_by('title')

    return render_modal_workflow(
        request, 'verdantimages/chooser/chooser.html', 'verdantimages/chooser/chooser.js',
        {'images': images}
    )


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

    return render_modal_workflow(
        request, None, 'verdantimages/chooser/image_chosen.js',
        {'image_json': image_json}
    )
