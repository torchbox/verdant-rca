# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations, models


def populate_programme_fields(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    ProgrammePage = apps.get_model('rca.ProgrammePage')
    ProgrammePageProgramme = apps.get_model('rca.ProgrammePageProgramme')

    for programme_page in ProgrammePage.objects.all().iterator():
        update_fields = []

        if programme_page.school:
            programme_page.school_new = School.objects.get(slug=programme_page.school)

            update_fields.append('school_new')

        if update_fields:
            programme_page.save(update_fields=update_fields)

    for programme_page_programme in ProgrammePageProgramme.objects.all().iterator():
        update_fields = []

        if programme_page_programme.programme:
            programme_page_programme.programme_new = Programme.objects.get(slug=programme_page_programme.programme_new)

            update_fields.append('programme_new')

        if update_fields:
            programme_page_programme.save(update_fields=update_fields)


def populate_programme_fields_revisions(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    ProgrammePage = apps.get_model('rca.ProgrammePage')

    for programme_page in ProgrammePage.objects.all().iterator():
        for revision in programme_page.revisions.all().iterator():
            content = json.loads(revision.content_json)
            changed = False

            if 'school' in content and not isinstance(content['school'], int):
                if content['school']:
                    content['school'] = School.objects.get(slug=content['school']).id
                else:
                    content['school'] = None

                changed = True

            if 'programmes' in content:
                for programme in content['programmes']:

                    if 'programme' in programme and not isinstance(programme['programme'], int):
                        if programme['programme']:
                            programme['programme'] = Programme.objects.get(slug=programme['programme']).id
                        else:
                            programme['programme'] = None

                        changed = True

            if changed:
                revision.content_json = json.dumps(content, cls=DjangoJSONEncoder)
                revision.save(update_fields=['content_json'])


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0028_taxonomy_programme_page_add_new_fields'),
    ]

    operations = [
        migrations.RunPython(populate_programme_fields, do_nothing),
        migrations.RunPython(populate_programme_fields_revisions, do_nothing),
    ]
