# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0016_auto_20151111_1519'),
    ]

    operations = [
        migrations.AddField(
            model_name='advert',
            name='promoted',
            field=models.BooleanField(default=False, help_text=b'Whether to show the advert at the top of the sidebar above all the other items.'),
        ),
    ]
