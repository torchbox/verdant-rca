from __future__ import with_statement
from fabric.api import *

env.roledefs = {
    'staging': ['django-staging.torchbox.com'],
    'production': ['rca2.dh.bytemark.co.uk'],
    #'production': ['rca2.dh.bytemark.co.uk', 'rca3.dh.bytemark.co.uk'],
}

@roles('staging')
def deploy_staging():
    with cd('/usr/local/django/verdant-rca/'):
        with settings(sudo_user='verdant-rca'):
            sudo("git pull")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/pip install -r django-verdant/requirements.txt")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py syncdb --settings=verdant.settings.production --noinput")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py migrate --settings=verdant.settings.production --noinput")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py collectstatic --settings=verdant.settings.production --noinput")

        sudo("supervisorctl restart verdant-rca")
        sudo("supervisorctl restart rca-celeryd")
        sudo("supervisorctl restart rca-celerybeat")

        with settings(sudo_user='verdant-rca'):
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py update_index --settings=verdant.settings.production")


@roles('production')
def deploy_production():
    with cd('/usr/local/django/verdant-rca/'):
        with settings(sudo_user='verdant-rca'):
            sudo("git pull")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/pip install -r django-verdant/requirements.txt")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py syncdb --settings=verdant.settings.production --noinput")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py migrate --settings=verdant.settings.production --noinput")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py collectstatic --settings=verdant.settings.production --noinput")

        sudo("supervisorctl restart verdant-rca")
        sudo("supervisorctl restart rca-celeryd")
        sudo("supervisorctl restart rca-celerybeat")

        with settings(sudo_user='verdant-rca'):
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py update_index --settings=verdant.settings.production")
