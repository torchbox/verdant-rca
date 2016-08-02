# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0027_auto_20160630_1520'),
    ]

    operations = [
        migrations.RenameField(
            model_name='newstudentpage',
            old_name='ma_programme_new',
            new_name='ma_programme',
        ),
        migrations.RenameField(
            model_name='newstudentpage',
            old_name='mphil_programme_new',
            new_name='mphil_programme',
        ),
        migrations.RenameField(
            model_name='newstudentpage',
            old_name='phd_programme_new',
            new_name='phd_programme',
        ),
    ]
