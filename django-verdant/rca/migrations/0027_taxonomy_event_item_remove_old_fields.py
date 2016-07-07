# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0026_taxonomy_event_item_migrate_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='eventitemrelatedarea',
            name='area',
        ),
        migrations.RemoveField(
            model_name='eventitemrelatedprogramme',
            name='programme',
        ),
        migrations.RemoveField(
            model_name='eventitemrelatedschool',
            name='school',
        ),
        migrations.RenameField(
            model_name='eventitemrelatedarea',
            old_name='area_new',
            new_name='area',
        ),
        migrations.RenameField(
            model_name='eventitemrelatedprogramme',
            old_name='programme_new',
            new_name='programme',
        ),
        migrations.RenameField(
            model_name='eventitemrelatedschool',
            old_name='school_new',
            new_name='school',
        ),
    ]
