# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0026_taxonomy_news_item_migrate_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='newsitemarea',
            name='area',
        ),
        migrations.RemoveField(
            model_name='newsitemrelatedprogramme',
            name='programme',
        ),
        migrations.RemoveField(
            model_name='newsitemrelatedschool',
            name='school',
        ),
        migrations.RenameField(
            model_name='newsitemarea',
            old_name='area_new',
            new_name='area',
        ),
        migrations.RenameField(
            model_name='newsitemrelatedprogramme',
            old_name='programme_new',
            new_name='programme',
        ),
        migrations.RenameField(
            model_name='newsitemrelatedschool',
            old_name='school_new',
            new_name='school',
        ),

        # Bonus!
        migrations.RemoveField(
            model_name='newsitem',
            name='area',
        ),
    ]
