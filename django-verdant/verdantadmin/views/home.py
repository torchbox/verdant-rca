from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from core.models import PageRevision

@login_required
def home(request):
    if request.user.has_perm('core.can_publish_page'):
        page_revisions_for_moderation = PageRevision.submitted_revisions.select_related('page', 'user').order_by('-created_at')
    else:
        page_revisions_for_moderation = PageRevision.objects.none()

    return render(request, "verdantadmin/home.html", {
        'page_revisions_for_moderation': page_revisions_for_moderation
    })
