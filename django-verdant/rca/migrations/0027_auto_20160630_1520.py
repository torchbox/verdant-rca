# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0026_populate_new_student_programme_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='newstudentpage',
            name='ma_programme',
        ),
        migrations.RemoveField(
            model_name='newstudentpage',
            name='ma_school',
        ),
        migrations.RemoveField(
            model_name='newstudentpage',
            name='mphil_programme',
        ),
        migrations.RemoveField(
            model_name='newstudentpage',
            name='mphil_school',
        ),
        migrations.RemoveField(
            model_name='newstudentpage',
            name='phd_programme',
        ),
        migrations.RemoveField(
            model_name='newstudentpage',
            name='phd_school',
        ),
    ]
