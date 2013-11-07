#!/bin/bash
# Script to run celerybeat that pushes periodic tasks to the queue
# Should be run on one server only!
/usr/local/django/virtualenvs/rca/bin/python /usr/local/django/verdant-rca/django-verdant/manage.py celerybeat
