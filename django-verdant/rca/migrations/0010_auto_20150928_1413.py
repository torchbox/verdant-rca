# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0009_auto_20150928_1342'),
    ]

    operations = [
        migrations.RenameField(
            model_name='homepage',
            old_name='alumni_stories',
            new_name='packery_student_stories',
        ),
        migrations.RemoveField(
            model_name='homepage',
            name='student_stories',
        ),
        migrations.AddField(
            model_name='homepage',
            name='packery_alumni_stories',
            field=models.IntegerField(help_text=b'', null=True, verbose_name=b'Number of alumni stories to show', choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]),
        ),
    ]
