from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required

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
    preview_image = image.get_rendition('max-130x100')

    return json.dumps({
        'id': image.id,
        'title': image.title,
        'preview': {
            'url': preview_image.url,
            'width': preview_image.width,
            'height': preview_image.height,
        }
    })

@login_required
def chooser(request):
    Image = get_image_model()
    ImageForm = get_image_form()
    uploadform = ImageForm()

    q = None
    if 'q' in request.GET or 'p' in request.GET:
        searchform = SearchForm(request.GET)
        if searchform.is_valid():
            q = searchform.cleaned_data['q']
            
            # page number
            p = request.GET.get("p", 1)
            
            images = Image.search(q, results_per_page=10, page=p)

            is_searching = True

        else:
            images = Image.objects.order_by('-created_at')
            p = request.GET.get("p", 1)
            paginator = Paginator(images, 10)

            try:
                images = paginator.page(p)
            except PageNotAnInteger:
                images = paginator.page(1)
            except EmptyPage:
                images = paginator.page(paginator.num_pages)
            
            is_searching = False

        return render(request, "verdantimages/chooser/results.html", {
            'images': images, 
            'is_searching': is_searching,
            'will_select_format': request.GET.get('select_format')
        })
    else:
        searchform = SearchForm()

        images = Image.objects.order_by('-created_at')
        p = request.GET.get("p", 1)
        paginator = Paginator(images, 10)

        try:
            images = paginator.page(p)
        except PageNotAnInteger:
            images = paginator.page(1)
        except EmptyPage:
            images = paginator.page(paginator.num_pages)
        

    return render_modal_workflow(request, 'verdantimages/chooser/chooser.html', 'verdantimages/chooser/chooser.js',{
        'images': images, 
        'uploadform': uploadform, 
        'searchform': searchform,
        'is_searching': False,
        'will_select_format': request.GET.get('select_format'),
        'popular_tags': Image.popular_tags(),
    })


@login_required
def image_chosen(request, image_id):
    image = get_object_or_404(get_image_model(), id=image_id)

    return render_modal_workflow(
        request, None, 'verdantimages/chooser/image_chosen.js',
        {'image_json': get_image_json(image)}
    )


@login_required
def chooser_upload(request):
    Image = get_image_model()
    ImageForm = get_image_form()

    if request.POST:
        image = Image(uploaded_by_user=request.user)
        form = ImageForm(request.POST, request.FILES, instance=image)

        if form.is_valid():
            form.save()
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


@login_required
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
