from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from core.models import PageRevision

@login_required
def home(request):
    page_revisions_for_moderation = PageRevision.submitted_revisions.select_related('page').order_by('-created_at')
    return render(request, "verdantadmin/home.html", {
        'page_revisions_for_moderation': page_revisions_for_moderation
    })
