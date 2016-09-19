from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig

from .signal_handlers import register_signal_handlers


class WebhooksAppConfig(AppConfig):
    name = 'webhooks'
    label = 'webhooks'
    verbose_name = "Webhooks"

    def ready(self):
        register_signal_handlers()
