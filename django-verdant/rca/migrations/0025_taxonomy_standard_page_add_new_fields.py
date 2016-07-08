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
            model_name='standardindex',
            name='events_feed_area_new',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, to='taxonomy.Area', help_text=b'', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='standardindex',
            name='news_carousel_area_new',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, to='taxonomy.Area', help_text=b'', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='standardindex',
            name='staff_feed_source_new',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, to='taxonomy.School', help_text=b'', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='standardpage',
            name='related_programme_new',
            field=models.ForeignKey(related_name='standard_pages', on_delete=django.db.models.deletion.SET_NULL, to='taxonomy.Programme', help_text=b'', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='standardpage',
            name='related_school_new',
            field=models.ForeignKey(related_name='standard_pages', on_delete=django.db.models.deletion.SET_NULL, to='taxonomy.School', help_text=b'', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='standardpage',
            name='related_area',
            field=models.ForeignKey(related_name='standard_pages', on_delete=django.db.models.deletion.SET_NULL, to='taxonomy.Area', help_text=b'', null=True, blank=True),
        ),
    ]
