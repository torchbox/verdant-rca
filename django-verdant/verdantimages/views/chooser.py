from django.shortcuts import get_object_or_404, render

import json

from verdantadmin.modal_workflow import render_modal_workflow
from verdantimages.models import get_image_model
from verdantimages.forms import get_image_form, ImageInsertionForm
from verdantadmin.forms import SearchForm
from verdantimages.formats import get_image_format


def get_image_json(image):
    """
    helper function: given an image, return the json to pass back to the
    image chooser panel
    """
    preview_image = image.get_rendition('fill-130x100')

    return json.dumps({
        'id': image.id,
        'title': image.title,
        'preview': {
            'url': preview_image.url,
            'width': preview_image.width,
            'height': preview_image.height,
        }
    })

def chooser(request):
    Image = get_image_model()
    ImageForm = get_image_form()

    uploadform = ImageForm()
    images = []
    if 'q' in request.GET:
        searchform = SearchForm(request.GET)
        if searchform.is_valid():
            q = searchform.cleaned_data['q']
            images = Image.search(q)
        return render(request, "verdantimages/chooser/search_results.html", {
            'images': images, 'will_select_format': request.GET.get('select_format')})
    else:
        searchform = SearchForm()

    return render_modal_workflow(
        request, 'verdantimages/chooser/chooser.html', 'verdantimages/chooser/chooser.js',
        {'images': images, 'uploadform': uploadform, 'searchform': searchform, 'will_select_format': request.GET.get('select_format')}
    )


def image_chosen(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    return render_modal_workflow(
        request, None, 'verdantimages/chooser/image_chosen.js',
        {'image_json': get_image_json(image)}
    )


def chooser_upload(request):
    Image = get_image_model()
    ImageForm = get_image_form()

    if request.POST:
        form = ImageForm(request.POST, request.FILES)

        if form.is_valid():
            image = form.save()
            if request.GET.get('select_format'):
                form = ImageInsertionForm(initial={'alt_text': image.default_alt_text})
                return render_modal_workflow(
                    request, 'verdantimages/chooser/select_format.html', 'verdantimages/chooser/select_format.js',
                    {'image': image, 'form': form}
                )
            else:
                # not specifying a format; return the image details now
                return render_modal_workflow(
                    request, None, 'verdantimages/chooser/image_chosen.js',
                    {'image_json': get_image_json(image)}
                )
    else:
        form = ImageForm()

    images = Image.objects.order_by('title')

    return render_modal_workflow(
        request, 'verdantimages/chooser/chooser.html', 'verdantimages/chooser/chooser.js',
        {'images': images, 'uploadform': form}
    )


def chooser_select_format(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    if request.POST:
        form = ImageInsertionForm(request.POST, initial={'alt_text': image.default_alt_text})
        if form.is_valid():

            format = get_image_format(form.cleaned_data['format'])
            preview_image = image.get_rendition(format.filter_spec)

            image_json = json.dumps({
                'id': image.id,
                'title': image.title,
                'format': format.name,
                'alt': form.cleaned_data['alt_text'],
                'class': format.classnames,
                'preview': {
                    'url': preview_image.url,
                    'width': preview_image.width,
                    'height': preview_image.height,
                },
                'html': format.image_to_editor_html(image, form.cleaned_data['alt_text']),
            })

            return render_modal_workflow(
                request, None, 'verdantimages/chooser/image_chosen.js',
                {'image_json': image_json}
            )
    else:
        form = ImageInsertionForm(initial={'alt_text': image.default_alt_text})

    return render_modal_workflow(
        request, 'verdantimages/chooser/select_format.html', 'verdantimages/chooser/select_format.js',
        {'image': image, 'form': form}
    )
