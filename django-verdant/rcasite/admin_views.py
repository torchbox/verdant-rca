from __future__ import unicode_literals

from django.conf import settings
from django.shortcuts import redirect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache

from wagtail.wagtailadmin.views import account


@sensitive_post_parameters()
@never_cache
def login(request):
    if settings.RCA_LOGIN_DISABLED and request.method == "POST":
        # Redirect back to this view and ignore the POST request
        redirect_to = request.path
        if request.POST.get('next', None) is not None:
            redirect_to += '?next=' + request.POST['next']

        return redirect(redirect_to)

    return account.login(request)
