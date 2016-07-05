# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def deduplicate_schools(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')

    schools = {}
    for school in School.objects.all():
        schools.setdefault(school.slug, school.id)

    for programme in Programme.objects.all():
        programme.school_id = schools[programme.school.slug]
        programme.save()

    School.objects.exclude(id__in=list(schools.values())).delete()


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0006_auto_20160615_1502'),
    ]

    operations = [
        migrations.RunPython(deduplicate_schools, do_nothing),
    ]
