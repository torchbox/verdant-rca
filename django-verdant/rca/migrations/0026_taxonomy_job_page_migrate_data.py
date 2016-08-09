# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations, models


def migrate_job_page_taxonomy(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    Area = apps.get_model('taxonomy.Area')
    JobPage = apps.get_model('rca.JobPage')

    for job_page in JobPage.objects.all().iterator():
        update_fields = []

        if job_page.school:
            if job_page.school in ['helenhamlyn', 'innovationrca']:
                job_page.area = Area.objects.get(slug=job_page.school)

                update_fields.append('area')
            else:
                # Remap
                if job_page.school == 'schooloffashiontextiles':
                    job_page.school = 'schoolofmaterial'

                job_page.school_new = School.objects.get(slug=job_page.school)

                update_fields.append('school_new')

        if job_page.programme:
            job_page.programme_new = Programme.objects.get(slug=job_page.programme)

            update_fields.append('programme_new')

        if update_fields:
            job_page.save(update_fields=update_fields)


def migrate_job_page_taxonomy_revisions(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    Area = apps.get_model('taxonomy.Area')
    JobPage = apps.get_model('rca.JobPage')

    for job_page in JobPage.objects.all().iterator():
        for revision in job_page.revisions.all().iterator():
            content = json.loads(revision.content_json)

            if content['school']:
                if content['school'] in ['helenhamlyn', 'innovationrca']:
                    content['area'] = Area.objects.get(slug=content['school']).id
                    content['school'] = None
                else:
                    # Remap
                    if content['school'] == 'schooloffashiontextiles':
                        content['school'] = 'schoolofmaterial'

                    content['school'] = School.objects.get(slug=content['school']).id
            else:
                content['school'] = None

            if content['programme']:
                content['programme'] = Programme.objects.get(slug=content['programme']).id
            else:
                content['programme'] = None

            revision.content_json = json.dumps(content, cls=DjangoJSONEncoder)
            revision.save(update_fields=['content_json'])


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0025_taxonomy_job_page_add_new_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_job_page_taxonomy, do_nothing),
        migrations.RunPython(migrate_job_page_taxonomy_revisions, do_nothing),
    ]
