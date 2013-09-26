from django.shortcuts import get_object_or_404

import json

from verdantadmin.modal_workflow import render_modal_workflow
from verdantsnippets.views.snippets import get_content_type_from_url_params, get_snippet_type_name

def choose(request, content_type_app_name, content_type_model_name):
    content_type = get_content_type_from_url_params(content_type_app_name, content_type_model_name)
    model = content_type.model_class()
    snippet_type_name = get_snippet_type_name(content_type)[0]

    items = model.objects.all()

    return render_modal_workflow(request,
        'verdantsnippets/chooser/choose.html', 'verdantsnippets/chooser/choose.js',
        {
            'content_type': content_type,
            'snippet_type_name': snippet_type_name,
            'items': items,
        }
    )

def chosen(request, content_type_app_name, content_type_model_name, id):
    content_type = get_content_type_from_url_params(content_type_app_name, content_type_model_name)
    model = content_type.model_class()
    item = get_object_or_404(model, id=id)

    snippet_json = json.dumps({
        'id': item.id,
        'string': unicode(item),
    })

    return render_modal_workflow(request,
        None, 'verdantsnippets/chooser/chosen.js',
        {
            'snippet_json': snippet_json,
        }
    )
