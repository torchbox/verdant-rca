# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2017-01-20 11:50
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0050_auto_20170120_1124'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='programmepageoursites',
            name='image',
        ),
        migrations.RemoveField(
            model_name='programmepageoursites',
            name='page',
        ),
        migrations.DeleteModel(
            name='ProgrammePageOurSites',
        ),
    ]