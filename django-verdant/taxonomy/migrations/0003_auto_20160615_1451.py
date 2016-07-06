# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0002_initial_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='programme',
            name='school',
            field=models.ForeignKey(related_name='programmes', to='taxonomy.School'),
        ),
    ]
