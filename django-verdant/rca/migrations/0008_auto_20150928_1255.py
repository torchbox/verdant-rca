# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import modelcluster.fields
import modelcluster.contrib.taggit


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        ('rca', '0007_auto_20150925_1333'),
    ]

    operations = [
        migrations.CreateModel(
            name='StandardPageTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content_object', modelcluster.fields.ParentalKey(related_name='tagged_items', to='rca.StandardPage')),
                ('tag', models.ForeignKey(related_name='rca_standardpagetag_items', to='taggit.Tag')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='homepage',
            name='alumni_stories',
            field=models.IntegerField(help_text=b'', null=True, verbose_name=b'Number of student stories to show', choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]),
        ),
        migrations.AddField(
            model_name='homepage',
            name='student_stories',
            field=models.IntegerField(help_text=b'', null=True, verbose_name=b'Number of student stories to show', choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]),
        ),
        migrations.AddField(
            model_name='standardpage',
            name='tags',
            field=modelcluster.contrib.taggit.ClusterTaggableManager(to='taggit.Tag', through='rca.StandardPageTag', help_text=b'Use the "student-story" or "alumni-story" tags to make this page appear in the homepage packery (if "Show on homepage" is ticked too).', verbose_name='Tags'),
        ),
    ]
