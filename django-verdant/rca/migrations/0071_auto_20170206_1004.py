# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2017-02-06 10:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0070_auto_20170206_0950'),
    ]

    operations = [
        migrations.RenameField(
            model_name='programmepage',
            old_name='ma_programme_overview',
            new_name='ma_programme_overview_link',
        ),
        migrations.RenameField(
            model_name='programmepage',
            old_name='ma_programme_staff',
            new_name='ma_programme_staff_link',
        ),
        migrations.AddField(
            model_name='programmepage',
            name='ma_programme_overview_link_text',
            field=models.CharField(blank=True, help_text=b'', max_length=255),
        ),
        migrations.AddField(
            model_name='programmepage',
            name='ma_programme_staff_link_text',
            field=models.CharField(blank=True, help_text=b'', max_length=255),
        ),
    ]
