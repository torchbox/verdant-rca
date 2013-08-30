from django.http import Http404

from core.models import Site


def serve(request, path):
    hostname = request.META['HTTP_HOST'].split(':')[0]

    # find a Site matching this specific hostname:
    try:
        site = Site.objects.get(hostname=hostname)
    except Site.DoesNotExist:
        # failing that, look for a catch-all Site
        try:
            site = Site.objects.get(hostname='*')
        except Site.DoesNotExist:
            raise Http404

    path_components = [component for component in path.split('/') if component]
    return site.root_page.specific.route(request, path_components)
