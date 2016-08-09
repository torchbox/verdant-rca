# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0026_taxonomy_rca_now_migrate_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rcanowpage',
            name='area',
        ),
        migrations.RemoveField(
            model_name='rcanowpage',
            name='programme',
        ),
        migrations.RemoveField(
            model_name='rcanowpage',
            name='school',
        ),
        migrations.RemoveField(
            model_name='rcanowpagearea',
            name='area',
        ),
        migrations.RenameField(
            model_name='rcanowpage',
            old_name='programme_new',
            new_name='programme',
        ),
        migrations.RenameField(
            model_name='rcanowpage',
            old_name='school_new',
            new_name='school',
        ),
        migrations.RenameField(
            model_name='rcanowpagearea',
            old_name='area_new',
            new_name='area',
        ),
    ]
