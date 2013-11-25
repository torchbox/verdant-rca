#!/bin/sh
# Script to run the celery daemon with the hostname-named queue.
exec /usr/local/django/virtualenvs/verdant-rca/bin/python /usr/local/django/verdant-rca/rcasite/manage.py celeryd

# Use separate queue for each server if there's more than one and if the local filesystem is accessed (e.g. async file uploads).
# /usr/local/django/virtualenvs/rca/bin/python /usr/local/django/verdant-rca/rcasite/manage.py celeryd -Q celery,`hostname`
