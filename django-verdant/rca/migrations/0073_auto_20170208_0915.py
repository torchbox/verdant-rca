# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2017-02-08 09:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0072_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='programmepagefindoutmore',
            name='link',
            field=models.ForeignKey(blank=True, help_text=b'', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='wagtailcore.Page'),
        ),
    ]
