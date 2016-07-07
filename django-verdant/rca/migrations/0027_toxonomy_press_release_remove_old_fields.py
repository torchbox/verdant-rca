# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0026_taxonomy_press_release_migrate_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pressrelease',
            name='area',
        ),
        migrations.RemoveField(
            model_name='pressreleasearea',
            name='area',
        ),
        migrations.RemoveField(
            model_name='pressreleaserelatedprogramme',
            name='programme',
        ),
        migrations.RemoveField(
            model_name='pressreleaserelatedschool',
            name='school',
        ),
        migrations.RenameField(
            model_name='pressreleasearea',
            old_name='area_new',
            new_name='area',
        ),
        migrations.RenameField(
            model_name='pressreleaserelatedprogramme',
            old_name='programme_new',
            new_name='programme',
        ),
        migrations.RenameField(
            model_name='pressreleaserelatedschool',
            old_name='school_new',
            new_name='school',
        ),
    ]
