# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import modelcluster.contrib.taggit


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0008_auto_20150928_1255'),
    ]

    operations = [
        migrations.AlterField(
            model_name='standardpage',
            name='tags',
            field=modelcluster.contrib.taggit.ClusterTaggableManager(to='taggit.Tag', through='rca.StandardPageTag', blank=True, help_text=b'Use the "student-story" or "alumni-story" tags to make this page appear in the homepage packery (if "Show on homepage" is ticked too).', verbose_name='Tags'),
        ),
    ]
