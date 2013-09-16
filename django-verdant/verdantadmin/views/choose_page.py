from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.http import Http404

from core.models import Page, get_page_types
from verdantadmin.modal_workflow import render_modal_workflow

def browse(request, content_type_app_name, content_type_model_name, parent_page_id=None):

    try:
        content_type = ContentType.objects.get_by_natural_key(content_type_app_name, content_type_model_name)
    except ContentType.DoesNotExist:
        raise Http404
    # content type must be in the list of page types
    if content_type not in get_page_types():
        raise Http404
    desired_class = content_type.model_class()

    if parent_page_id:
        parent_page = get_object_or_404(Page, id=parent_page_id)
    else:
        parent_page = Page.get_first_root_node()

    pages = parent_page.get_children().order_by('title')

    # restrict the page listing to just those pages that:
    # - are of the given content type (taking into account class inheritance)
    # - or can be navigated into (i.e. have children)

    shown_pages = []
    for page in pages:
        can_choose = issubclass(page.specific_class, desired_class)
        can_descend = page.get_children_count()

        if can_choose or can_descend:
            shown_pages.append({
                'page': page, 'can_choose': can_choose, 'can_descend': can_descend,
            })

    return render_modal_workflow(request,
        'verdantadmin/choose_page/browse.html', 'verdantadmin/choose_page/browse.js',
        {
            'content_type_app_name': content_type_app_name,
            'content_type_model_name': content_type_model_name,
            'parent_page': parent_page,
            'pages': shown_pages,
        }
    )
