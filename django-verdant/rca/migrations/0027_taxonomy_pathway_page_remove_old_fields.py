# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0026_taxonomy_pathway_page_migrate_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pathwaypage',
            name='related_programme',
        ),
        migrations.RemoveField(
            model_name='pathwaypage',
            name='related_school',
        ),
        migrations.RenameField(
            model_name='pathwaypage',
            old_name='related_programme_new',
            new_name='related_programme',
        ),
        migrations.RenameField(
            model_name='pathwaypage',
            old_name='related_school_new',
            new_name='related_school',
        ),
    ]
