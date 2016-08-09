# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0017_auto_20160630_1103'),
        ('rca', '0024_pagealias'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='innovationrcaproject',
            name='programme',
        ),
        migrations.RemoveField(
            model_name='innovationrcaproject',
            name='school',
        ),
        migrations.RemoveField(
            model_name='reachoutrcaproject',
            name='programme',
        ),
        migrations.RemoveField(
            model_name='reachoutrcaproject',
            name='school',
        ),
    ]
