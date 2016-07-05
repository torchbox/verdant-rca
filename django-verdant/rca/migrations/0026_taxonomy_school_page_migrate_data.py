# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations, models


def populate_school_new_school_field(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    SchoolPage = apps.get_model('rca.SchoolPage')

    for school_page in SchoolPage.objects.all().iterator():
        update_fields = []

        if school_page.school:
            school_page.school_new = School.objects.get(slug=school_page.school)

            update_fields.append('school_new')

        if update_fields:
            school_page.save(update_fields=update_fields)


def populate_school_new_school_field_revisions(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    SchoolPage = apps.get_model('rca.SchoolPage')

    for school_page in SchoolPage.objects.all().iterator():
        for revision in school_page.revisions.all().iterator():
            content = json.loads(revision.content_json)
            changed = False

            if 'school' in content and not isinstance(content['school'], int):
                if content['school']:
                    content['school'] = School.objects.get(slug=content['school']).id
                else:
                    content['school'] = None

                changed = True

            if changed:
                revision.content_json = json.dumps(content, cls=DjangoJSONEncoder)
                revision.save(update_fields=['content_json'])


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0025_taxonomy_school_page_add_new_fields'),
    ]

    operations = [
        migrations.RunPython(populate_school_new_school_field, do_nothing),
        migrations.RunPython(populate_school_new_school_field_revisions, do_nothing),
    ]
