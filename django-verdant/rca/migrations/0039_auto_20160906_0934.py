# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailredirects', '0004_set_unique_on_path_and_site'),
        ('wagtailcore', '0020_add_index_on_page_first_published_at'),
        ('wagtailforms', '0002_add_verbose_names'),
        ('wagtailsearchpromotions', '0001_initial'),
        ('rca', '0038_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='alumniindex',
            name='feed_image',
        ),
        migrations.RemoveField(
            model_name='alumniindex',
            name='page_ptr',
        ),
        migrations.RemoveField(
            model_name='alumniindex',
            name='social_image',
        ),
        migrations.RemoveField(
            model_name='alumniindexad',
            name='ad',
        ),
        migrations.RemoveField(
            model_name='alumniindexad',
            name='page',
        ),
        migrations.RemoveField(
            model_name='alumniindexrelatedlink',
            name='link',
        ),
        migrations.RemoveField(
            model_name='alumniindexrelatedlink',
            name='page',
        ),
        migrations.RemoveField(
            model_name='alumnipage',
            name='feed_image',
        ),
        migrations.RemoveField(
            model_name='alumnipage',
            name='page_ptr',
        ),
        migrations.RemoveField(
            model_name='alumnipage',
            name='profile_image',
        ),
        migrations.RemoveField(
            model_name='alumnipage',
            name='social_image',
        ),
        migrations.DeleteModel(
            name='AlumniIndex',
        ),
        migrations.DeleteModel(
            name='AlumniIndexAd',
        ),
        migrations.DeleteModel(
            name='AlumniIndexRelatedLink',
        ),
        migrations.DeleteModel(
            name='AlumniPage',
        ),
    ]
