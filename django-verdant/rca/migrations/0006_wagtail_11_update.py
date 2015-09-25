# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0005_wagtail_10_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='rcaimage',
            name='file_size',
            field=models.PositiveIntegerField(null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='rcaimage',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created at', db_index=True),
        ),
    ]
