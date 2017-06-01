# vim:sw=4 ts=4 et:
from __future__ import with_statement
from fabric.api import *
from fabric.colors import red

import uuid

env.roledefs = {
    'staging': ['rca@by-staging-1.torchbox.com'],

    'nginx': ['root@rca1.torchbox.com'],

    # All hosts will be listed here.
    'production': ['rca@web-1-a.rca.bmyrk.torchbox.net', 'rca@web-1-b.rca.bmyrk.torchbox.net'],
}
MIGRATION_SERVER = 'web-1-a.rca.bmyrk.torchbox.net'


@roles('staging')
def deploy_staging(branch="staging", gitonly=False):
    run("git fetch")
    run("git checkout %s" % branch)
    run("git pull")
    run("pip install -r django-verdant/requirements.txt")
    if not gitonly:
        run("python django-verdant/manage.py migrate --settings=rcasite.settings.staging --noinput")
    run("python django-verdant/manage.py collectstatic --settings=rcasite.settings.staging --noinput")
    run("python django-verdant/manage.py compress --settings=rcasite.settings.staging")

    run('restart')


@roles('production')
def deploy(gitonly=False):
    run("git pull")
    run("pip install -r django-verdant/requirements.txt")

    if env['host'] == MIGRATION_SERVER:
        if not gitonly:
            run("python django-verdant/manage.py migrate --settings=rcasite.settings.production --noinput")

    run("python django-verdant/manage.py collectstatic --settings=rcasite.settings.production --noinput")
    run("python django-verdant/manage.py compress --settings=rcasite.settings.production")

    run("restart")


@roles('nginx')
def clear_cache():
    puts(red('WARNING: clearing the nginx cache requires sudo, ask sysadmin if it fails'))
    run('find /var/cache/nginx -type f -delete')


@runs_once
@roles('production')
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


@runs_once
@roles('production')
def fetch_live_media():
    remote_path = '/verdant-shared/media/'

    local('rsync -avz %s:%s /vagrant/media/' % (env['host_string'], remote_path))


@roles('staging')
def fetch_staging_data():
    filename = "verdant_rca_%s.sql" % uuid.uuid4()
    local_path = "/tmp/%s" % filename
    remote_path = "/tmp/%s" % filename

    run('pg_dump -cf %s rcawagtail' % remote_path)
    run('gzip %s' % remote_path)
    get("%s.gz" % remote_path, "%s.gz" % local_path)
    run('rm %s.gz' % remote_path)
    local('dropdb verdant')
    local('createdb verdant')
    local('gunzip %s.gz' % local_path)
    local('psql verdant -f %s' % local_path)
    local('rm %s' % local_path)


@runs_once
@roles('production')
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
    run("rsync -avz rca@web-1-b.rca.bmyrk.torchbox.net:/verdant-shared/media/ /usr/local/django/rcawagtail/django-verdant/media/")


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
