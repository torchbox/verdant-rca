# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.CharField(unique=True, max_length=255)),
                ('display_name', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['display_name'],
            },
        ),
        migrations.CreateModel(
            name='Programme',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.CharField(help_text=b'Like the slug field above, this field must not change year-on-year and it must only contain lowercase letters.', max_length=255)),
                ('display_name', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['display_name'],
            },
        ),
        migrations.CreateModel(
            name='School',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('year', models.PositiveIntegerField(help_text=b"This is the year that the academic year finishes. For example, this should be set to '2017' for the '2016/17' academic year")),
                ('slug', models.CharField(help_text=b'This field is used to link this school with previous years. The display name may be changed year-on-year but the slug must remain the same. It must contain lowercase letters only.', max_length=255)),
                ('display_name', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['-year', 'display_name'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='school',
            unique_together=set([('year', 'slug')]),
        ),
        migrations.AddField(
            model_name='programme',
            name='school',
            field=modelcluster.fields.ParentalKey(related_name='programmes', to='taxonomy.School'),
        ),
        migrations.AlterUniqueTogether(
            name='programme',
            unique_together=set([('school', 'slug')]),
        ),
    ]
