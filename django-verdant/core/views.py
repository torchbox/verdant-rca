from django.http import Http404

from core.models import Site


def serve(request, path):
    try:
        site = Site.find_for_request(request)
    except Site.DoesNotExist:
        raise Http404

    path_components = [component for component in path.split('/') if component]
    return site.root_page.specific.route(request, path_components)
