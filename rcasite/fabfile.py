from __future__ import with_statement
from fabric.api import *

env.roledefs = {
    'staging': ['django-staging.torchbox.com'],

    'squid': ['root@rca1.dh.bytemark.co.uk'],
    # All hosts will be listed here.
    'production': ['root@rca2.dh.bytemark.co.uk', 'root@rca3.dh.bytemark.co.uk'],
}
MIGRATION_SERVER = 'rca2.dh.bytemark.co.uk'

@roles('staging')
def deploy_staging():
    with cd('/usr/local/django/verdant-rca/'):
        with settings(sudo_user='verdant-rca'):
            sudo("git pull")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/pip install -r rcasite/requirements.txt")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python rcasite/manage.py syncdb --settings=verdant.settings.staging --noinput")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python rcasite/manage.py migrate --settings=verdant.settings.staging --noinput")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python rcasite/manage.py collectstatic --settings=verdant.settings.staging --noinput")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python rcasite/manage.py compress --settings=verdant.settings.staging")

        sudo("supervisorctl restart verdant-rca")
        sudo("supervisorctl restart rca-celeryd")
        sudo("supervisorctl restart rca-celerybeat")

        with settings(sudo_user='verdant-rca'):
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python rcasite/manage.py update_index --settings=verdant.settings.staging")


@roles('production')
def deploy():
    with cd('/usr/local/django/verdant-rca/'):
        with settings(sudo_user='verdant-rca'):
            sudo("git pull")
            sudo("/usr/local/django/virtualenvs/verdant-rca/bin/pip install -r rcasite/requirements.txt")

            if env['host'] == MIGRATION_SERVER:
                sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python rcasite/manage.py syncdb --settings=verdant.settings.production --noinput")
                sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python rcasite/manage.py migrate --settings=verdant.settings.production --noinput")
                sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python rcasite/manage.py collectstatic --settings=verdant.settings.production --noinput")
                sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python rcasite/manage.py compress --settings=verdant.settings.production")

            run("supervisorctl restart verdant-rca")
            run("supervisorctl restart rca-celeryd")
            if env['host'] == MIGRATION_SERVER:
                run("supervisorctl restart rca-celerybeat")
                sudo("/usr/local/django/virtualenvs/verdant-rca/bin/python rcasite/manage.py update_index --settings=verdant.settings.production")

@roles('squid')
def clear_cache():
    run('squidclient -p 80 -m PURGE http://www.rca.ac.uk')
