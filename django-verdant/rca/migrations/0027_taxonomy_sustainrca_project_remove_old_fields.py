# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0026_taxonomy_sustainrca_project_migrate_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sustainrcaproject',
            name='programme',
        ),
        migrations.RemoveField(
            model_name='sustainrcaproject',
            name='school',
        ),
        migrations.RenameField(
            model_name='sustainrcaproject',
            old_name='programme_new',
            new_name='programme',
        ),
        migrations.RenameField(
            model_name='sustainrcaproject',
            old_name='school_new',
            new_name='school',
        ),
    ]
