from __future__ import with_statement
from fabric.api import *

env.roledefs = {
    'staging': ['root@django-staging.torchbox.com'],
    # This is the host where migrations are done.
    'production_primary': ['root@rca2.dh.bytemark.co.uk'],
    # All hosts will be listed here.
    'production': ['root@rca2.dh.bytemark.co.uk', 'root@rca3.dh.bytemark.co.uk'],
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
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py compress --settings=verdant.settings.production")

        sudo("supervisorctl restart verdant-rca")
        sudo("supervisorctl restart rca-celeryd")
        sudo("supervisorctl restart rca-celerybeat")

        with settings(sudo_user='verdant-rca'):
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py update_index --settings=verdant.settings.production")


@roles('production')
def deploy():
    with cd('/usr/local/django/verdant-rca/'):
        with settings(sudo_user='verdant-rca'):
            sudo("git pull")

    run("supervisorctl restart verdant-rca")

@roles('production_primary')
def migrate():
    with cd('/usr/local/django/verdant-rca/'):
        with settings(sudo_user='verdant-rca'):
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/pip install -r django-verdant/requirements.txt")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py syncdb --settings=verdant.settings.production --noinput")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py migrate --settings=verdant.settings.production --noinput")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py collectstatic --settings=verdant.settings.production --noinput")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py compress --settings=verdant.settings.production")

        run("supervisorctl restart verdant-rca")
        run("supervisorctl restart rca-celeryd")
        run("supervisorctl restart rca-celerybeat")

        with settings(sudo_user='verdant-rca'):
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py update_index --settings=verdant.settings.production")
