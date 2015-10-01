# vim:sw=4 ts=4 et:
from __future__ import with_statement
from fabric.api import *
from fabric.colors import red

import uuid

env.roledefs = {
    'staging': ['rcawagtail@by-staging-1.torchbox.com'],

    'nginx': ['root@rca1.torchbox.com'],
    'db': ['root@rca1.torchbox.com'],
    'db-notroot': ['rca1.torchbox.com'],
    'rca2': ['rcawagtail@rca2.bmyrk.torchbox.net'],

    # All hosts will be listed here.
    'production': ['rcawagtail@rca2.bmyrk.torchbox.net', 'rcawagtail@rca3.bmyrk.torchbox.net'],
}
MIGRATION_SERVER = 'rca2.bmyrk.torchbox.net'


@roles('staging')
def deploy_staging(branch="staging", gitonly=False):
    with cd('/usr/local/django/rcawagtail/'):
        run("git fetch")
        run("git checkout %s" % branch)
        run("git pull")
        run("/usr/local/django/virtualenvs/rcawagtail/bin/pip install -r django-verdant/requirements.txt")
        if not gitonly:
            run("/usr/local/django/virtualenvs/rcawagtail/bin/python django-verdant/manage.py syncdb --settings=rcasite.settings.staging --noinput")
            run("/usr/local/django/virtualenvs/rcawagtail/bin/python django-verdant/manage.py migrate --settings=rcasite.settings.staging --noinput")
        run("/usr/local/django/virtualenvs/rcawagtail/bin/python django-verdant/manage.py collectstatic --settings=rcasite.settings.staging --noinput")
        run("/usr/local/django/virtualenvs/rcawagtail/bin/python django-verdant/manage.py compress --settings=rcasite.settings.staging")

        run('restart')

        if not gitonly:
            run("/usr/local/django/virtualenvs/rcawagtail/bin/python django-verdant/manage.py update_index --settings=rcasite.settings.staging")


@roles('production')
def deploy(gitonly=False):
    with cd('/usr/local/django/rcawagtail/'):
        run("git pull")
        run("/usr/local/django/virtualenvs/rcawagtail/bin/pip install -r django-verdant/requirements.txt")

        if env['host'] == MIGRATION_SERVER:
            if not gitonly:
                run("/usr/local/django/virtualenvs/rcawagtail/bin/python django-verdant/manage.py migrate --settings=rcasite.settings.production --noinput")

            run("/usr/local/django/virtualenvs/rcawagtail/bin/python django-verdant/manage.py collectstatic --settings=rcasite.settings.production --noinput")
            run("/usr/local/django/virtualenvs/rcawagtail/bin/python django-verdant/manage.py compress --settings=rcasite.settings.production")

        run("restart")
        if env['host'] != MIGRATION_SERVER and not gitonly:
            run("/usr/local/django/virtualenvs/rcawagtail/bin/python django-verdant/manage.py update_index --settings=rcasite.settings.production")


@roles('nginx')
def clear_cache():
    puts(red('WARNING: clearing the nginx cache requires sudo, ask sysadmin if it fails'))
    run('find /var/cache/nginx -type f -delete')


@roles('rca2')
def fetch_live_data():
    filename = "verdant_rca_%s.sql" % uuid.uuid4()
    local_path = "/tmp/%s" % filename
    remote_path = "/tmp/%s" % filename

    run('pg_dump -cf %s verdant_rca' % remote_path)
    run('gzip %s' % remote_path)
    get("%s.gz" % remote_path, "%s.gz" % local_path)
    run('rm %s.gz' % remote_path)
    local('dropdb verdant')
    local('createdb verdant')
    local('gunzip %s.gz' % local_path)
    local('psql verdant -f %s' % local_path)
    local('rm %s' % local_path)


@roles('rca2')
def staging_fetch_live_data():
    filename = "verdant_rca_%s.sql" % uuid.uuid4()
    local_path = "/usr/local/django/rcawagtail/tmp/%s" % filename
    remote_path = "/tmp/%s" % filename

    run('pg_dump -cf %s verdant_rca' % remote_path)
    run('gzip %s' % remote_path)
    get("%s.gz" % remote_path, "%s.gz" % local_path)
    run('rm %s.gz' % remote_path)
    local('gunzip %s.gz' % local_path)
    local('psql rcawagtail -f %s' % local_path)
    local('rm %s' % local_path)


@roles('staging')
def sync_staging_with_live():
    env.forward_agent = True
    run('fab staging_fetch_live_data')
    run("django-admin.py migrate --settings=rcasite.settings.staging --noinput")
    run("rsync -avz rcawagtail@rca2.bmyrk.torchbox.net:/verdant-shared/media/ /usr/local/django/rcawagtail/django-verdant/media/")


@roles('production')
def run_show_reports(year="2014"):
    with cd('/usr/local/django/verdant-rca/'):
        with settings(sudo_user='verdant-rca'):
            if env['host'] == MIGRATION_SERVER:
                sudo('/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py students_report django-verdant/graduating_students.csv %s --settings=rcasite.settings.production' % year)
                get('report.csv', 'students_report.csv')
                get('report.html', 'students_report.html')
                sudo('rm report.csv')
                sudo('rm report.html')

                sudo('/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py postcard_dump %s --settings=rcasite.settings.production' % year)
                get('postcard_dump.zip', 'postcard_dump.zip')
                sudo('rm postcard_dump.zip')

                sudo('/usr/local/django/virtualenvs/verdant-rca/bin/python django-verdant/manage.py profile_image_dump django-verdant/graduating_students.csv %s --settings=rcasite.settings.production' % year)
                get('profile_image_dump.zip', 'profile_image_dump.zip')
                sudo('rm profile_image_dump.zip')
