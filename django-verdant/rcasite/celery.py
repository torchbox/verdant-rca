from __future__ import absolute_import

# FROM: http://celery.readthedocs.org/en/latest/django/first-steps-with-django.html

import os

from celery import Celery

from django.conf import settings

# NOTE: DJANGO_SETTINGS_MODULE gets set by Puppet on production servers
# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rcasite.settings.dev')

app = Celery('rca')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
