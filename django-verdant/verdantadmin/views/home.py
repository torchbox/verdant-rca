from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings

from core.models import Page, PageRevision, UserPagePermissionsProxy
from verdantimages.models import get_image_model
from verdantdocs.models import Document

@login_required
def home(request):
    user_perms = UserPagePermissionsProxy(request.user)
    page_revisions_for_moderation = user_perms.revisions_for_moderation().select_related('page', 'user').order_by('-created_at')

    # Last n edited pages
    last_edits = PageRevision.objects.filter(user=request.user).order_by('-created_at')[:5]

    total_images = get_image_model().objects.count()
    total_documents = Document.objects.count()
    total_pages = Page.objects.count() - 1  # subtract 1 because the root node is not a real page

    return render(request, "verdantadmin/home.html", {
        'total_pages': total_pages,
        'total_images': total_images,
        'total_docs': total_documents,
        'site_name': settings.VERDANT_SITE_NAME,
        'page_revisions_for_moderation': page_revisions_for_moderation,
        'last_edits':last_edits,
        'user':request.user
    })


def error_test(request):
    raise Exception("This is a test of the emergency broadcast system.")
