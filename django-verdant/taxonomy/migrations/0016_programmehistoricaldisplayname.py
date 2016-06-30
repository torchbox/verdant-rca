# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0015_auto_20160630_1055'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProgrammeHistoricalDisplayName',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('end_year', models.PositiveIntegerField(help_text=b'This is the last year that the name was used. For example, ifthe name was changed at the beginning of the 2016/17 academicyear, this field should be set to 2016.')),
                ('display_name', models.CharField(max_length=255)),
                ('school', modelcluster.fields.ParentalKey(related_name='historical_display_names', to='taxonomy.Programme')),
            ],
            options={
                'ordering': ['end_year'],
            },
        ),
    ]
