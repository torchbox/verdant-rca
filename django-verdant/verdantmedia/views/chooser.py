from verdantadmin.modal_workflow import render_modal_workflow
from verdantmedia.forms import MediaForm


def chooser(request):
    form = MediaForm()

    return render_modal_workflow(request, 'verdantmedia/chooser/chooser.html', 'verdantmedia/chooser/chooser.js',{
        'form': form, 
    })