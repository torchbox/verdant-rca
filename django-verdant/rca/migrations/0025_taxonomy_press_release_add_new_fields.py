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
            model_name='pressreleasearea',
            name='area_new',
            field=models.ForeignKey(related_name='press_releases', on_delete=django.db.models.deletion.SET_NULL, to='taxonomy.Area', help_text=b'', null=True),
        ),
        migrations.AddField(
            model_name='pressreleaserelatedprogramme',
            name='programme_new',
            field=models.ForeignKey(related_name='press_releases', on_delete=django.db.models.deletion.SET_NULL, to='taxonomy.Programme', help_text=b'', null=True),
        ),
        migrations.AddField(
            model_name='pressreleaserelatedschool',
            name='school_new',
            field=models.ForeignKey(related_name='press_releases', on_delete=django.db.models.deletion.SET_NULL, to='taxonomy.School', help_text=b'', null=True),
        ),
    ]
