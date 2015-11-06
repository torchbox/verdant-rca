# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0006_wagtail_11_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='homepage',
            name='packery_events_rcatalks',
            field=models.IntegerField(help_text=b'', null=True, verbose_name=b'Number of RCA Talk events to show', choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]),
        ),
        migrations.AlterField(
            model_name='homepage',
            name='packery_events',
            field=models.IntegerField(help_text=b'', null=True, verbose_name=b'Number of events to show (excluding RCA Talks)', choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]),
        ),
    ]
