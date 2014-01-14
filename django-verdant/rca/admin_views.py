# RCA-specific extensions to Verdant admin.

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rca.models import RcaNowPage, RcaNowIndex

@login_required
def rca_now_index(request):
    try:
        index_page = RcaNowIndex.objects.all()[0]
    except IndexError:
        raise Exception('This site does not have an RCA Now section (using the RcaNowIndex page type)')

    pages = RcaNowPage.objects.filter(owner=request.user)
    return render(request, 'rca/admin/rca_now_index.html', {
        'rca_now_index': index_page,
        'pages': pages,
    })
