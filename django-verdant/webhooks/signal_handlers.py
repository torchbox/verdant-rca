from __future__ import absolute_import, unicode_literals

import logging

import requests
from requests.exceptions import RequestException

from django.conf import settings

from wagtail.wagtailcore.signals import page_published, page_unpublished


logger = logging.getLogger('webhooks')


def call_webhook(url, page):
    url = url.format(
        type=page._meta.app_label + '.' + page.__class__.__name__,
        id=page.id,
    )

    try:
        response = requests.post(url, data={
            'page_id': page.id,
            'page_url': page.full_url,
        })

        if response.status_code != 200:
            logger.error("Non-successful status code returned while calling webhook (got %s %s)", response.status_code, response.reason)

    except RequestException as e:
        logger.exception("RequestException raised while calling webhook")


def page_published_signal_handler(instance, **kwargs):
    for url in getattr(settings, 'WEBHOOKS_PAGE_PUBLISHED', []):
        call_webhook(url, instance)


def page_unpublished_signal_handler(instance, **kwargs):
    for url in getattr(settings, 'WEBHOOKS_PAGE_UNPUBLISHED', []):
       call_webhook(url, instance)


def register_signal_handlers():
    if getattr(settings, 'WEBHOOKS_PAGE_PUBLISHED', None):
        page_published.connect(page_published_signal_handler)

    if getattr(settings, 'WEBHOOKS_PAGE_UNPUBLISHED', None):
        page_unpublished.connect(page_unpublished_signal_handler)
