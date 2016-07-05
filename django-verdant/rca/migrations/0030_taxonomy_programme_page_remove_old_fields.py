# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0029_taxonomy_programme_page_migrate_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='programmepage',
            name='school',
        ),
        migrations.RemoveField(
            model_name='programmepageprogramme',
            name='programme',
        ),
        migrations.RenameField(
            model_name='programmepage',
            old_name='school_new',
            new_name='school',
        ),
        migrations.RenameField(
            model_name='programmepageprogramme',
            old_name='programme_new',
            new_name='programme',
        ),
    ]
