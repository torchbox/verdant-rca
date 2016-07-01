# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0026_auto_20160701_1417'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='staffpage',
            name='school',
        ),
        migrations.RemoveField(
            model_name='staffpagerole',
            name='area',
        ),
        migrations.RemoveField(
            model_name='staffpagerole',
            name='programme',
        ),
        migrations.RemoveField(
            model_name='staffpagerole',
            name='school',
        ),
    ]
