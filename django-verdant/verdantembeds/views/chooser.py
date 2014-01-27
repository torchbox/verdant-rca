from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from verdantembeds.forms import EmbedForm
from verdantembeds.format import embed_to_editor_html
from django.forms.util import ErrorList


def chooser(request):
    form = EmbedForm()

    return render_modal_workflow(request, 'verdantembeds/chooser/chooser.html', 'verdantembeds/chooser/chooser.js',{
        'form': form, 
    })


def chooser_upload(request):
    if request.POST:
        form = EmbedForm(request.POST, request.FILES)

        if form.is_valid():
            embed_html = embed_to_editor_html(form.cleaned_data['url'])
            if embed_html != "":
                return render_modal_workflow(
                    request, None, 'verdantembeds/chooser/embed_chosen.js',
                    {'embed_html': embed_html}
                )
            else:
                errors = form._errors.setdefault('url', ErrorList())
                errors.append('This URL is not recognised')
                return render_modal_workflow(request, 'verdantembeds/chooser/chooser.html', 'verdantembeds/chooser/chooser.js',{
                    'form': form, 
                })
    else:
        form = EmbedForm()

    return render_modal_workflow(request, 'verdantembeds/chooser/chooser.html', 'verdantembeds/chooser/chooser.js',{
        'form': form, 
    })