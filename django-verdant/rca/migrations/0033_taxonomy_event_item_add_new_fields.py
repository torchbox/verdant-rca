# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0018_auto_20160808_0954'),
        ('rca', '0032_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventitem',
            name='area_new',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, to='taxonomy.Area', help_text=b'', null=True),
        ),
    ]
