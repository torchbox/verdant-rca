# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def deduplicate_programmes(apps, schema_editor):
    """
    Before this migration, each programme had a separate record for each
    year.

    This migration removes all but the latest copy of the programme from the
    database, as we're about to remove the graduation_year field.
    """
    Programme = apps.get_model('taxonomy.Programme')
    programmes_to_keep = list(Programme.objects.order_by('slug', '-graduation_year').distinct('slug').values_list('id', flat=True))
    Programme.objects.exclude(id__in=programmes_to_keep).delete()


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration



class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0011_auto_20160621_1448'),
    ]

    operations = [
        migrations.RunPython(deduplicate_programmes, do_nothing),
    ]
