# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0003_booleanfield_default_value'),
    ]

    operations = [
        migrations.AlterField(
            model_name='oeformpage',
            name='feed_image',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio.', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rcablogindex',
            name='feed_image',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio.', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rcablogpage',
            name='feed_image',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio.', null=True),
            preserve_default=True,
        ),
    ]
