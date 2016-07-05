# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0007_deduplicate_schools'),
    ]

    operations = [
        migrations.AlterField(
            model_name='school',
            name='slug',
            field=models.CharField(unique=True, max_length=255),
        ),
    ]
