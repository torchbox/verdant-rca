# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def populate_programme_disabled(apps, schema_editor):
    """
    The previous data migration (0012) removed all duplicate programmes keeping
    only the latest one.

    If the latest programme was not 2017, then that programme should be marked
    as disabled.
    """
    Programme = apps.get_model('taxonomy.Programme')

    Programme.objects.filter(graduation_year__lt=2017).update(disabled=True)


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0013_programme_disabled'),
    ]

    operations = [
        migrations.RunPython(populate_programme_disabled, do_nothing),
    ]
