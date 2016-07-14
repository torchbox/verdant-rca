# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0026_taxonomy_blog_migrate_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rcablogpage',
            name='area',
        ),
        migrations.RemoveField(
            model_name='rcablogpage',
            name='programme',
        ),
        migrations.RemoveField(
            model_name='rcablogpage',
            name='school',
        ),
        migrations.RemoveField(
            model_name='rcablogpagearea',
            name='area',
        ),
        migrations.RenameField(
            model_name='rcablogpage',
            old_name='programme_new',
            new_name='programme',
        ),
        migrations.RenameField(
            model_name='rcablogpage',
            old_name='school_new',
            new_name='school',
        ),
        migrations.RenameField(
            model_name='rcablogpagearea',
            old_name='area_new',
            new_name='area',
        ),
    ]
