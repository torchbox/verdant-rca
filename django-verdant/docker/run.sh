#!/bin/bash
django-admin compress --force
/app/bin/proximo gunicorn rcasite.wsgi:application