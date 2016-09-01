# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations, models


def migrate_sustainrca_project_taxonomy(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    SustainRCAProject = apps.get_model('rca.SustainRCAProject')

    for sustainrca_project in SustainRCAProject.objects.all().iterator():
        update_fields = []

        if sustainrca_project.school and sustainrca_project.school:
            sustainrca_project.school_new = School.objects.get(slug=sustainrca_project.school)

            update_fields.append('school_new')

        if sustainrca_project.programme:
            sustainrca_project.programme_new = Programme.objects.get(slug=sustainrca_project.programme)

            update_fields.append('programme_new')

        if update_fields:
            sustainrca_project.save(update_fields=update_fields)


def migrate_sustainrca_project_taxonomy_revisions(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    Area = apps.get_model('taxonomy.Area')
    SustainRCAProject = apps.get_model('rca.SustainRCAProject')

    for sustainrca_project in SustainRCAProject.objects.all().iterator():
        for revision in sustainrca_project.revisions.all().iterator():
            content = json.loads(revision.content_json)

            if content['school'] and content['school']:
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
        ('rca', '0025_taxonomy_sustainrca_project_add_new_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_sustainrca_project_taxonomy, do_nothing),
        migrations.RunPython(migrate_sustainrca_project_taxonomy_revisions, do_nothing),
    ]
