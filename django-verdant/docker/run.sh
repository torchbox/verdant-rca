#!/bin/bash
django-admin compress --force
bin/proxmi gunicorn rcasite.wsgi:application