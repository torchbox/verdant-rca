# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca_show', '0007_auto_20160628_1605'),
    ]

    operations = [
        migrations.AddField(
            model_name='showindexpage',
            name='hide_animation_videos',
            field=models.BooleanField(default=True, help_text=b'If this box is checked, videos embedded in the carousel will not be displayed on Animation and Visual Communication student profiles'),
        ),
    ]
