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
            model_name='newstudentpage',
            name='ma_programme_new',
            field=models.ForeignKey(related_name='ma_students', on_delete=django.db.models.deletion.SET_NULL, verbose_name=b'Programme', to='taxonomy.Programme', help_text=b'', null=True),
        ),
        migrations.AddField(
            model_name='newstudentpage',
            name='mphil_programme_new',
            field=models.ForeignKey(related_name='mphil_students', on_delete=django.db.models.deletion.SET_NULL, verbose_name=b'Programme', to='taxonomy.Programme', help_text=b'', null=True),
        ),
        migrations.AddField(
            model_name='newstudentpage',
            name='phd_programme_new',
            field=models.ForeignKey(related_name='phd_students', on_delete=django.db.models.deletion.SET_NULL, verbose_name=b'Programme', to='taxonomy.Programme', help_text=b'', null=True),
        ),
    ]
