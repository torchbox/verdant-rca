# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0003_auto_20160615_1451'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='programme',
            options={'ordering': ['-graduation_year', 'display_name']},
        ),
        migrations.AddField(
            model_name='programme',
            name='graduation_year',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AlterUniqueTogether(
            name='programme',
            unique_together=set([('graduation_year', 'slug')]),
        ),
    ]
