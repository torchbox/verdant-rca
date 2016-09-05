# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations, models


def migrate_alumni_page_taxonomy(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    Area = apps.get_model('taxonomy.Area')
    AlumniPage = apps.get_model('rca.AlumniPage')

    for alumni_page in AlumniPage.objects.all().iterator():
        update_fields = []

        if alumni_page.school:
            # Remap
            if alumni_page.school == 'schoolofappliedart':
                # School of Applied Art contained programmes that are now part of School of Material
                # www.rca.ac.uk/documents/120/1RCA_Annual_Review_2009-10.pdf
                alumni_page.school = 'schoolofmaterial'

            alumni_page.school_new = School.objects.get(slug=alumni_page.school)

            update_fields.append('school_new')
        if alumni_page.programme:
            alumni_page.programme_new = Programme.objects.get(slug=alumni_page.programme)

            update_fields.append('programme_new')

        if update_fields:
            alumni_page.save(update_fields=update_fields)


def migrate_alumni_page_taxonomy_revisions(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    Area = apps.get_model('taxonomy.Area')
    AlumniPage = apps.get_model('rca.AlumniPage')

    for alumni_page in AlumniPage.objects.all().iterator():
        for revision in alumni_page.revisions.all().iterator():
            content = json.loads(revision.content_json)

            if content['school']:
                # Remap
                if content['school'] == 'schoolofappliedart':
                    # School of Applied Art contained programmes that are now part of School of Material
                    # www.rca.ac.uk/documents/120/1RCA_Annual_Review_2009-10.pdf
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
        ('rca', '0025_taxonomy_alumni_page_add_new_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_alumni_page_taxonomy, do_nothing),
        migrations.RunPython(migrate_alumni_page_taxonomy_revisions, do_nothing),
    ]
