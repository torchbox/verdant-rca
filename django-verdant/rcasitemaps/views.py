from __future__ import absolute_import, unicode_literals

from django.contrib.sitemaps import views as sitemap_views

from .sitemap_generator import Sitemap


def index(request, sitemaps, **kwargs):
    sitemaps = prepare_sitemaps(request, sitemaps)

    # Workaround: Override the HTTP_HOST and set it as the wagtail.site.hostname value
    # rather than the host django will set. This is to ensure the sitempat index view
    # lists all the pages using the hostname set in the wagtail site object, otherwise
    # the absolute urls on the index listing would begin https://www.mysite.herokuapp.com/...
    request.META['HTTP_HOST'] = request.site.hostname
    return sitemap_views.index(request, sitemaps, **kwargs)


def sitemap(request, sitemaps=None, **kwargs):
    if sitemaps:
        sitemaps = prepare_sitemaps(request, sitemaps)
    else:
        sitemaps = {'wagtail': Sitemap(request.site)}
    return sitemap_views.sitemap(request, sitemaps, **kwargs)


def prepare_sitemaps(request, sitemaps):
    """Intialize the wagtail Sitemap by passing the request.site value. """
    initialised_sitemaps = {}
    for name, sitemap_cls in sitemaps.items():
        if issubclass(sitemap_cls, Sitemap):
            initialised_sitemaps[name] = sitemap_cls(request.site)
        else:
            initialised_sitemaps[name] = sitemap_cls
    return initialised_sitemaps
