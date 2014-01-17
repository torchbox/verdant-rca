#!/bin/sh
# Script to run celerybeat that pushes periodic tasks to the queue
# Should be run on one server only!
exec /usr/local/django/virtualenvs/verdant-rca/bin/python /usr/local/django/verdant-rca/django-verdant/manage.py celerybeat --settings=verdant.settings.staging
