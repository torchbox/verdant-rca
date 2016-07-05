# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def populate_programme_graduation_year(apps, schema_editor):
    Programme = apps.get_model('taxonomy.Programme')

    for programme in Programme.objects.all():
        programme.graduation_year = programme.school.year
        programme.save()


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0004_auto_20160615_1455'),
    ]

    operations = [
        migrations.RunPython(populate_programme_graduation_year, do_nothing),
    ]
