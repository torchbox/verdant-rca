# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2017-07-06 21:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0087_staffpage_migrate_area_data_to_roles'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='staffpage',
            name='area',
        ),
        migrations.RemoveField(
            model_name='staffpage',
            name='staff_location',
        ),
        migrations.AddField(
            model_name='staffpagerole',
            name='location',
            field=models.CharField(blank=True, choices=[(b'ceramicsgsmj', b'Ceramics, Glass, Metalwork & Jewellery'), (b'darwinworshops', b'Darwin Workshops'), (b'fashiontextiles', b'Fashion & Textiles'), (b'lensbasedmediaaudio', b'Lens-based Media and Audio'), (b'paintingsculpture', b'Painting & Sculpture'), (b'printmakingletterpress', b'Printmaking & Letterpress'), (b'rapidform', b'Rapidform')], help_text=b'', max_length=255),
        ),
        migrations.AlterField(
            model_name='staffpage',
            name='staff_type',
            field=models.CharField(choices=[(b'academic', b'Academic'), (b'technical', b'Technical'), (b'administrative', b'Administrative')], help_text=b'', max_length=255),
        ),
        migrations.AlterField(
            model_name='staffpagerole',
            name='title',
            field=models.CharField(help_text=b'', max_length=255, verbose_name=b'Job title'),
        ),
    ]
