# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2018-09-17 10:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0092_programmepage_poster_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='homepage',
            name='use_2018_redesign_template',
            field=models.BooleanField(default=False),
        ),
    ]
