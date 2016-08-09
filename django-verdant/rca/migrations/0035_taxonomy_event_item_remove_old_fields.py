# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0034_taxonomy_event_item_migrate_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='eventitem',
            name='area',
        ),
        migrations.RemoveField(
            model_name='eventitem',
            name='external_link',
        ),
        migrations.RemoveField(
            model_name='eventitem',
            name='external_link_text',
        ),
        migrations.RenameField(
            model_name='eventitem',
            old_name='area_new',
            new_name='area',
        ),
    ]
