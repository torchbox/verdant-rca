# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0009_auto_20160621_1357'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchoolHistoricalDisplayName',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('end_year', models.PositiveIntegerField()),
                ('display_name', models.CharField(max_length=255)),
                ('school', modelcluster.fields.ParentalKey(related_name='historical_display_names', to='taxonomy.School')),
            ],
            options={
                'ordering': ['end_year'],
            },
        ),
    ]
