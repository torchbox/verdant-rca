# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0012_deduplicate_programmes'),
    ]

    operations = [
        migrations.AddField(
            model_name='programme',
            name='disabled',
            field=models.BooleanField(default=False),
        ),
    ]
