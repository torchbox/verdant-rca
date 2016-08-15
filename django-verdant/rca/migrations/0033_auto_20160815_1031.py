# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0032_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newstudentpage',
            name='ma_programme',
            field=models.ForeignKey(related_name='ma_students', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='taxonomy.Programme', help_text=b'', null=True, verbose_name=b'Programme'),
        ),
        migrations.AlterField(
            model_name='newstudentpage',
            name='mphil_programme',
            field=models.ForeignKey(related_name='mphil_students', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='taxonomy.Programme', help_text=b'', null=True, verbose_name=b'Programme'),
        ),
        migrations.AlterField(
            model_name='newstudentpage',
            name='phd_programme',
            field=models.ForeignKey(related_name='phd_students', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='taxonomy.Programme', help_text=b'', null=True, verbose_name=b'Programme'),
        ),
    ]
