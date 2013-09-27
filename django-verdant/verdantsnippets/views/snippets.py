from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.encoding import force_text
from django.utils.text import capfirst
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages

from verdantsnippets.models import get_snippet_content_types
from verdantadmin.edit_handlers import ObjectList, get_form_for_model, extract_panel_definitions_from_form_class

# == Helper functions ==

def get_snippet_type_name(content_type):
    """ e.g. given the 'advert' content type, return ('Advert', 'Adverts') """
    # why oh why is this so convoluted?
    opts = content_type.model_class()._meta
    return (
        force_text(opts.verbose_name),
        force_text(opts.verbose_name_plural)
    )

def get_content_type_from_url_params(app_name, model_name):
    """
    retrieve a content type from an app_name / model_name combo.
    Throw Http404 if not a valid snippet type
    """
    try:
        content_type = ContentType.objects.get_by_natural_key(app_name, model_name)
    except ContentType.DoesNotExist:
        raise Http404
    if content_type not in get_snippet_content_types():
        # don't allow people to hack the URL to edit content types that aren't registered as snippets
        raise Http404

    return content_type

SNIPPET_EDIT_HANDLERS = {}
def get_snippet_edit_handler(model):
    if model not in SNIPPET_EDIT_HANDLERS:
        if hasattr(model, 'panels'):
            edit_handler = ObjectList(model.panels)
            # form = edit_handler.get_form_class()
        else:
            form = get_form_for_model(model)
            panels = extract_panel_definitions_from_form_class(form)
            edit_handler = ObjectList(panels)

        SNIPPET_EDIT_HANDLERS[model] = edit_handler

    return SNIPPET_EDIT_HANDLERS[model]

# == Views ==

def index(request):
    snippet_types = [
        (
            get_snippet_type_name(content_type)[1],
            content_type
        )
        for content_type in get_snippet_content_types()
    ]
    return render(request, 'verdantsnippets/snippets/index.html', {
        'snippet_types': snippet_types,
    })


def list(request, content_type_app_name, content_type_model_name):
    content_type = get_content_type_from_url_params(content_type_app_name, content_type_model_name)
    model = content_type.model_class()
    snippet_type_name, snippet_type_name_plural = get_snippet_type_name(content_type)

    items = model.objects.all()

    return render(request, 'verdantsnippets/snippets/list.html', {
        'content_type': content_type,
        'snippet_type_name': snippet_type_name,
        'snippet_type_name_plural': snippet_type_name_plural,
        'items': items,
    })


def create(request, content_type_app_name, content_type_model_name):
    content_type = get_content_type_from_url_params(content_type_app_name, content_type_model_name)
    model = content_type.model_class()
    snippet_type_name = get_snippet_type_name(content_type)[0]

    instance = model()
    edit_handler_class = get_snippet_edit_handler(model)
    form_class = edit_handler_class.get_form_class(model)

    if request.POST:
        form = form_class(request.POST, request.FILES, instance=instance)
        edit_handler = edit_handler_class(request.POST, request.FILES, instance=instance, form=form)

        if all([form.is_valid(), edit_handler.is_valid()]):
            edit_handler.pre_save()
            form.save()
            edit_handler.post_save()

            messages.success(
                request,
                "%s '%s' created." % (capfirst(get_snippet_type_name(content_type)[0]), instance)
            )
            return redirect('verdantsnippets_list', content_type.app_label, content_type.model)
    else:
        form = form_class(instance=instance)
        edit_handler = edit_handler_class(instance=instance, form=form)

    return render(request, 'verdantsnippets/snippets/create.html', {
        'content_type': content_type,
        'snippet_type_name': snippet_type_name,
        'edit_handler': edit_handler,
    })

def edit(request, content_type_app_name, content_type_model_name, id):
    content_type = get_content_type_from_url_params(content_type_app_name, content_type_model_name)
    model = content_type.model_class()
    snippet_type_name = get_snippet_type_name(content_type)[0]

    instance = get_object_or_404(model, id=id)
    edit_handler_class = get_snippet_edit_handler(model)
    form_class = edit_handler_class.get_form_class(model)

    if request.POST:
        form = form_class(request.POST, request.FILES, instance=instance)
        edit_handler = edit_handler_class(request.POST, request.FILES, instance=instance, form=form)

        if all([form.is_valid(), edit_handler.is_valid()]):
            edit_handler.pre_save()
            form.save()
            edit_handler.post_save()

            messages.success(
                request,
                "%s '%s' updated." % (capfirst(snippet_type_name), instance)
            )
            return redirect('verdantsnippets_list', content_type.app_label, content_type.model)
    else:
        form = form_class(instance=instance)
        edit_handler = edit_handler_class(instance=instance, form=form)

    return render(request, 'verdantsnippets/snippets/edit.html', {
        'content_type': content_type,
        'snippet_type_name': snippet_type_name,
        'instance': instance,
        'edit_handler': edit_handler,
    })


def delete(request, content_type_app_name, content_type_model_name, id):
    content_type = get_content_type_from_url_params(content_type_app_name, content_type_model_name)
    model = content_type.model_class()
    snippet_type_name = get_snippet_type_name(content_type)[0]

    instance = get_object_or_404(model, id=id)

    if request.POST:
        instance.delete()
        messages.success(
            request,
            "%s '%s' deleted." % (capfirst(snippet_type_name), instance)
        )
        return redirect('verdantsnippets_list', content_type.app_label, content_type.model)

    return render(request, 'verdantsnippets/snippets/confirm_delete.html', {
        'content_type': content_type,
        'snippet_type_name': snippet_type_name,
        'instance': instance,
    })
