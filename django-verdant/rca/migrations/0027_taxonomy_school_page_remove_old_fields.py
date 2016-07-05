# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0026_taxonomy_school_page_migrate_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='schoolpage',
            name='school',
        ),
        migrations.RenameField(
            model_name='schoolpage',
            old_name='school_new',
            new_name='school',
        ),
    ]
