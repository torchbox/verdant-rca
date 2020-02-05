from __future__ import absolute_import, unicode_literals

from django.contrib.sitemaps import views as sitemap_views

from django.contrib.sites.shortcuts import get_current_site
from django.core import urlresolvers
from django.template.response import TemplateResponse
from .sitemap_generator import Sitemap


def sitemap_views_index(request, sitemaps,
          template_name='sitemap_index.xml', content_type='application/xml',
          sitemap_url_name='django.contrib.sitemaps.views.sitemap'):

    req_protocol = request.scheme
    req_site = get_current_site(request)

    sites = []
    for section, site in sitemaps.items():
        if callable(site):
            site = site()
        protocol = req_protocol if site.protocol is None else site.protocol
        sitemap_url = urlresolvers.reverse(
            sitemap_url_name, kwargs={'section': section})
        absolute_url = '%s://%s%s' % (protocol, request.site.hostname, sitemap_url)
        sites.append(absolute_url)
        for page in range(2, site.paginator.num_pages + 1):
            sites.append('%s?p=%s' % (absolute_url, page))

    return TemplateResponse(request, template_name, {'sitemaps': sites},
                            content_type=content_type)

def index(request, sitemaps, **kwargs):
    sitemaps = prepare_sitemaps(request, sitemaps)
    return sitemap_views_index(request, sitemaps, **kwargs)


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