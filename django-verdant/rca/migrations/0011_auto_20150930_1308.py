# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0010_auto_20150928_1413'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='homepage',
            name='packery_alumni',
        ),
        migrations.AlterField(
            model_name='homepage',
            name='packery_alumni_stories',
            field=models.IntegerField(blank=True, help_text=b'', null=True, verbose_name=b'Number of alumni stories to show', choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)]),
        ),
        migrations.AlterField(
            model_name='homepage',
            name='packery_blog',
            field=models.IntegerField(blank=True, help_text=b'', null=True, verbose_name=b'Number of blog items to show', choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)]),
        ),
        migrations.AlterField(
            model_name='homepage',
            name='packery_events',
            field=models.IntegerField(blank=True, help_text=b'', null=True, verbose_name=b'Number of events to show (excluding RCA Talks)', choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)]),
        ),
        migrations.AlterField(
            model_name='homepage',
            name='packery_events_rcatalks',
            field=models.IntegerField(blank=True, help_text=b'', null=True, verbose_name=b'Number of RCA Talk events to show', choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)]),
        ),
        migrations.AlterField(
            model_name='homepage',
            name='packery_news',
            field=models.IntegerField(blank=True, help_text=b'', null=True, verbose_name=b'Number of news items to show', choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)]),
        ),
        migrations.AlterField(
            model_name='homepage',
            name='packery_rcanow',
            field=models.IntegerField(blank=True, help_text=b'', null=True, verbose_name=b'Number of RCA Now items to show', choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)]),
        ),
        migrations.AlterField(
            model_name='homepage',
            name='packery_research',
            field=models.IntegerField(blank=True, help_text=b'', null=True, verbose_name=b'Number of research items to show', choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)]),
        ),
        migrations.AlterField(
            model_name='homepage',
            name='packery_review',
            field=models.IntegerField(blank=True, help_text=b'', null=True, verbose_name=b'Number of reviews to show', choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)]),
        ),
        migrations.AlterField(
            model_name='homepage',
            name='packery_staff',
            field=models.IntegerField(blank=True, help_text=b'', null=True, verbose_name=b'Number of staff to show', choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)]),
        ),
        migrations.AlterField(
            model_name='homepage',
            name='packery_student_stories',
            field=models.IntegerField(blank=True, help_text=b'', null=True, verbose_name=b'Number of student stories to show', choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)]),
        ),
        migrations.AlterField(
            model_name='homepage',
            name='packery_student_work',
            field=models.IntegerField(blank=True, help_text=b'Student pages flagged to Show On Homepage must have at least one carousel item', null=True, verbose_name=b'Number of student work items to show', choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)]),
        ),
        migrations.AlterField(
            model_name='homepage',
            name='packery_tweets',
            field=models.IntegerField(blank=True, help_text=b'', null=True, verbose_name=b'Number of tweets to show', choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)]),
        ),
    ]
