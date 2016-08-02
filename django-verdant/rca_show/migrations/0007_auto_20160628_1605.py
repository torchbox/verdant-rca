# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca_show', '0006_auto_20160628_1549'),
    ]

    operations = [
        migrations.AlterField(
            model_name='showindexpageprogramme',
            name='programme_new',
            field=models.ForeignKey(related_name='+', verbose_name=b'Programme', to='taxonomy.Programme'),
        ),
        migrations.AlterField(
            model_name='showindexprogrammeintro',
            name='programme_new',
            field=models.ForeignKey(related_name='+', verbose_name=b'Programme', to='taxonomy.Programme'),
        ),
        migrations.RemoveField(
            model_name='showindexpageprogramme',
            name='programme',
        ),
        migrations.RemoveField(
            model_name='showindexprogrammeintro',
            name='programme',
        ),
        migrations.RenameField(
            model_name='showindexpageprogramme',
            old_name='programme_new',
            new_name='programme',
        ),
        migrations.RenameField(
            model_name='showindexprogrammeintro',
            old_name='programme_new',
            new_name='programme',
        ),
    ]
