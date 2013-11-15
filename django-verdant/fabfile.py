from __future__ import with_statement
from fabric.api import *

env.roledefs = {
    'staging': ['django-staging.torchbox.com'],
    'production': ['rca2.dh.bytemark.co.uk'],
}

@roles('staging')
def deploy_staging():
    with cd('/usr/local/django/verdant-rca/'):
        with settings(sudo_user='verdant-rca'):
            sudo("git pull")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/pip install -r django-verdant/requirements.txt")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py syncdb --noinput")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py migrate --noinput")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py collectstatic --noinput")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py compress")

        sudo("supervisorctl restart verdant-rca")
        # MW 2013-11-13 - leave celery disabled while we diagnose runaway memory usage
        #sudo("supervisorctl restart rca-celeryd")
        #sudo("supervisorctl restart rca-celerybeat")

        with settings(sudo_user='verdant-rca'):
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py update_index")


@roles('production')
def deploy_production():
    with cd('/usr/local/django/verdant-rca/'):
        with settings(sudo_user='verdant-rca'):
            sudo("git pull")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/pip install -r django-verdant/requirements.txt")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py syncdb --noinput")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py migrate --noinput")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py collectstatic --noinput")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py compress")

        sudo("supervisorctl restart verdant-rca")
        # MW 2013-11-13 - leave celery disabled while we diagnose runaway memory usage
        #sudo("supervisorctl restart rca-celeryd")
        #sudo("supervisorctl restart rca-celerybeat")

        with settings(sudo_user='verdant-rca'):
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py update_index")
