#!/bin/bash
django-admin compress --force
gunicorn rcasite.wsgi:application