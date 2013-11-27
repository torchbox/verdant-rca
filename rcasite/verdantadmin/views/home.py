from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings

from core.models import Page, PageRevision
from verdantimages.models import get_image_model
from verdant.verdantdocs.models import Document

@login_required
def home(request):
    if request.user.has_perm('core.can_publish_page'):
        page_revisions_for_moderation = PageRevision.submitted_revisions.select_related('page', 'user').order_by('-created_at')
    else:
        page_revisions_for_moderation = PageRevision.objects.none()

    total_images = get_image_model().objects.count()
    total_documents = Document.objects.count()
    total_pages = Page.objects.count()


    return render(request, "verdantadmin/home.html", {
        'total_pages': total_pages,
        'total_images': total_images,
        'total_docs': total_documents,
        'site_name': settings.VERDANT_SITE_NAME,
        'page_revisions_for_moderation': page_revisions_for_moderation
    })


def error_test(request):
    raise Exception("This is a test of the emergency broadcast system.")
