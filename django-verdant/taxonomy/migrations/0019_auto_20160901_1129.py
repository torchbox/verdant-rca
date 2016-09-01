# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0018_auto_20160808_0954'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='programme',
            options={'ordering': ['display_name']},
        ),
    ]
