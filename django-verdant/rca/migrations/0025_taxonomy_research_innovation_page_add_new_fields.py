# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0017_auto_20160630_1103'),
        ('rca', '0024_pagealias'),
    ]

    operations = [
        migrations.AddField(
            model_name='researchinnovationpage',
            name='news_carousel_area_new',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='taxonomy.Area', help_text=b'', null=True),
        ),
    ]
