#!/bin/bash
django-admin compress --force
bin/proximo gunicorn rcasite.wsgi:application