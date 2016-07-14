# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0026_taxonomy_research_migrate_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='researchitem',
            name='programme',
        ),
        migrations.RemoveField(
            model_name='researchitem',
            name='school',
        ),
        migrations.RenameField(
            model_name='researchitem',
            old_name='programme_new',
            new_name='programme',
        ),
        migrations.RenameField(
            model_name='researchitem',
            old_name='school_new',
            new_name='school',
        ),
    ]
