# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0026_taxonomy_standard_page_migrate_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='standardindex',
            name='events_feed_area',
        ),
        migrations.RemoveField(
            model_name='standardindex',
            name='news_carousel_area',
        ),
        migrations.RemoveField(
            model_name='standardindex',
            name='staff_feed_source',
        ),
        migrations.RemoveField(
            model_name='standardpage',
            name='related_programme',
        ),
        migrations.RemoveField(
            model_name='standardpage',
            name='related_school',
        ),
        migrations.RenameField(
            model_name='standardindex',
            old_name='events_feed_area_new',
            new_name='events_feed_area',
        ),
        migrations.RenameField(
            model_name='standardindex',
            old_name='news_carousel_area_new',
            new_name='news_carousel_area',
        ),
        migrations.RenameField(
            model_name='standardindex',
            old_name='staff_feed_source_new',
            new_name='staff_feed_source',
        ),
        migrations.RenameField(
            model_name='standardpage',
            old_name='related_programme_new',
            new_name='related_programme',
        ),
        migrations.RenameField(
            model_name='standardpage',
            old_name='related_school_new',
            new_name='related_school',
        ),
    ]
