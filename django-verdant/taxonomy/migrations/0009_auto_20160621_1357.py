# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0008_auto_20160615_1506'),
    ]

    operations = [
        migrations.AlterField(
            model_name='programme',
            name='graduation_year',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
    ]
