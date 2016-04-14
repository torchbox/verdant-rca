# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca_ee', '0005_courseneedsupload'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='courseneedsupload',
            name='page',
        ),
        migrations.DeleteModel(
            name='CourseNeedsUpload',
        ),
    ]
