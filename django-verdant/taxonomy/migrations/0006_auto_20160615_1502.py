# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0005_populate_programme_graduation_year'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='school',
            options={'ordering': ['display_name']},
        ),
        migrations.AlterField(
            model_name='programme',
            name='slug',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='school',
            name='slug',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='school',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='school',
            name='year',
        ),
    ]
