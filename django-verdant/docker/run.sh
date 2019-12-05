#!/bin/bash
django-admin compress --force
# QuotaGuard qgtunnel is used to connect to an external service, in this case
# LDAP, via a Static IP through a tunnel opened on the serve
 /app/bin/qgtunnel gunicorn rcasite.wsgi:application