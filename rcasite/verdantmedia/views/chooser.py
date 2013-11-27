from verdant.verdantadmin.modal_workflow import render_modal_workflow
from verdantmedia.forms import MediaForm
from verdantmedia.format import media_to_editor_html
from django.forms.util import ErrorList


def chooser(request):
    form = MediaForm()

    return render_modal_workflow(request, 'verdantmedia/chooser/chooser.html', 'verdantmedia/chooser/chooser.js',{
        'form': form, 
    })


def chooser_upload(request):
    if request.POST:
        form = MediaForm(request.POST, request.FILES)

        if form.is_valid():
            media_html = media_to_editor_html(form.cleaned_data['url'])
            if media_html != "":
                return render_modal_workflow(
                    request, None, 'verdantmedia/chooser/media_chosen.js',
                    {'media_html': media_html}
                )
            else:
                errors = form._errors.setdefault('url', ErrorList())
                errors.append('This URL is not recognised')
                return render_modal_workflow(request, 'verdantmedia/chooser/chooser.html', 'verdantmedia/chooser/chooser.js',{
                    'form': form, 
                })
    else:
        form = MediaForm()

    return render_modal_workflow(request, 'verdantmedia/chooser/chooser.html', 'verdantmedia/chooser/chooser.js',{
        'form': form, 
    })