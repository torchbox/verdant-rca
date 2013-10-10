from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.utils.http import urlencode

from core.models import Page
from verdantadmin.modal_workflow import render_modal_workflow
from verdantadmin.forms import ExternalLinkChooserForm, ExternalLinkChooserWithLinkTextForm, EmailLinkChooserForm, EmailLinkChooserWithLinkTextForm

def get_querystring(request):
    return urlencode({
        'page_type': request.GET.get('page_type', ''),
        'allow_external_link': request.GET.get('allow_external_link', ''),
        'allow_email_link': request.GET.get('allow_email_link', ''),
        'prompt_for_link_text': request.GET.get('prompt_for_link_text', ''),
    })

def browse(request, parent_page_id=None):

    page_type = request.GET.get('page_type') or 'core.page'
    content_type_app_name, content_type_model_name = page_type.split('.')
    try:
        content_type = ContentType.objects.get_by_natural_key(content_type_app_name, content_type_model_name)
    except ContentType.DoesNotExist:
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
            'allow_external_link': request.GET.get('allow_external_link'),
            'allow_email_link': request.GET.get('allow_email_link'),
            'querystring': get_querystring(request),
            'parent_page': parent_page,
            'pages': shown_pages,
        }
    )

def external_link(request):
    prompt_for_link_text = bool(request.GET.get('prompt_for_link_text'))

    if prompt_for_link_text:
        form_class = ExternalLinkChooserWithLinkTextForm
    else:
        form_class = ExternalLinkChooserForm

    if request.POST:
        form = form_class(request.POST)
        if form.is_valid():
            return render_modal_workflow(request,
                None, 'verdantadmin/choose_page/external_link_chosen.js',
                {
                    'url': form.cleaned_data['url'],
                    'link_text': form.cleaned_data['link_text'] if prompt_for_link_text else form.cleaned_data['url']
                }
            )
    else:
        form = form_class()

    return render_modal_workflow(request,
        'verdantadmin/choose_page/external_link.html', 'verdantadmin/choose_page/external_link.js',
        {
            'querystring': get_querystring(request),
            'allow_email_link': request.GET.get('allow_email_link'),
            'form': form,
        }
    )

def email_link(request):
    prompt_for_link_text = bool(request.GET.get('prompt_for_link_text'))

    if prompt_for_link_text:
        form_class = EmailLinkChooserWithLinkTextForm
    else:
        form_class = EmailLinkChooserForm

    if request.POST:
        form = form_class(request.POST)
        if form.is_valid():
            return render_modal_workflow(request,
                None, 'verdantadmin/choose_page/external_link_chosen.js',
                {
                    'url': 'mailto:' + form.cleaned_data['email_address'],
                    'link_text': form.cleaned_data['link_text'] if (prompt_for_link_text and form.cleaned_data['link_text']) else form.cleaned_data['email_address']
                }
            )
    else:
        form = form_class()

    return render_modal_workflow(request,
        'verdantadmin/choose_page/email_link.html', 'verdantadmin/choose_page/email_link.js',
        {
            'querystring': get_querystring(request),
            'allow_external_link': request.GET.get('allow_external_link'),
            'form': form,
        }
    )
