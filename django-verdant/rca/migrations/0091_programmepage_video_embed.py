# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2018-04-11 15:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0090_head_of_programme_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='programmepage',
            name='video_embed',
            field=models.URLField(blank=True, help_text=b'The video embed displayed underneath the contact bar.'),
        ),
    ]
