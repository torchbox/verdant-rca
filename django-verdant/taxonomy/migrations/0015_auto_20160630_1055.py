# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0014_populate_programme_disabled'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='programme',
            options={'ordering': ['display_name']},
        ),
        migrations.AlterField(
            model_name='programme',
            name='slug',
            field=models.CharField(unique=True, max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='programme',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='programme',
            name='graduation_year',
        ),
    ]
