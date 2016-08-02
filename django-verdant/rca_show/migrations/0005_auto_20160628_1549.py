# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0011_auto_20160621_1448'),
        ('rca_show', '0004_auto_20160225_1055'),
    ]

    operations = [
        migrations.AddField(
            model_name='showindexpageprogramme',
            name='programme_new',
            field=models.ForeignKey(related_name='+', verbose_name=b'Programme', to='taxonomy.Programme', null=True),
        ),
        migrations.AddField(
            model_name='showindexprogrammeintro',
            name='programme_new',
            field=models.ForeignKey(related_name='+', verbose_name=b'Programme', to='taxonomy.Programme', null=True),
        ),
    ]
