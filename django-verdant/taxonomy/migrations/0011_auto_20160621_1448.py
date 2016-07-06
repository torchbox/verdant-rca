# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0010_schoolhistoricaldisplayname'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schoolhistoricaldisplayname',
            name='end_year',
            field=models.PositiveIntegerField(help_text=b'This is the last year that the name was used. For example, ifthe name was changed at the beginning of the 2016/17 academicyear, this field should be set to 2016.'),
        ),
    ]
