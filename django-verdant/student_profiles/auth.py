
from __future__ import unicode_literals

from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.contrib.auth.views import logout as auth_logout, login as auth_login
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache

from wagtail.wagtailadmin import forms


@sensitive_post_parameters()
@never_cache
def login(request):
    if request.user.is_authenticated():
        return redirect('student-profiles:overview')
    else:
        # RCA wants to allow users to log-in with either their @rca.ac.uk email address or just their username portion
        # of it so we simply cut off everything after the first '@' in the username field. Simple hack!
        if 'username' in request.POST and '@' in request.POST['username']:
            request.POST = request.POST.copy()
            request.POST['username'] = request.POST['username'][:request.POST['username'].index('@')]

        request.GET = request.GET.copy()
        request.GET.setdefault('next', reverse('student-profiles:overview'))
        return auth_login(request,
            template_name='student_profiles/login.html',
            authentication_form=forms.LoginForm,
        )


def logout(request):
    response = auth_logout(request, next_page='student-profiles:login')

    # By default, logging out will generate a fresh sessionid cookie. We want to use the
    # absence of sessionid as an indication that front-end pages are being viewed by a
    # non-logged-in user and are therefore cacheable, so we forcibly delete the cookie here.
    response.delete_cookie(settings.SESSION_COOKIE_NAME,
        domain=settings.SESSION_COOKIE_DOMAIN,
        path=settings.SESSION_COOKIE_PATH)

    # HACK: pretend that the session hasn't been modified, so that SessionMiddleware
    # won't override the above and write a new cookie.
    request.session.modified = False

    return response
