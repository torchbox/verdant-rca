# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0027_auto_20160701_1513'),
    ]

    operations = [
        migrations.RenameField(
            model_name='staffpagerole',
            old_name='area_new',
            new_name='area',
        ),
        migrations.RenameField(
            model_name='staffpagerole',
            old_name='programme_new',
            new_name='programme',
        ),
        migrations.RenameField(
            model_name='staffpagerole',
            old_name='school_new',
            new_name='school',
        ),
        migrations.AlterField(
            model_name='staffpagerole',
            name='area',
            field=models.ForeignKey(related_name='staff_roles', on_delete=models.deletion.SET_NULL, blank=True, to='taxonomy.Area', help_text=b'', null=True),
        ),
        migrations.AlterField(
            model_name='staffpagerole',
            name='programme',
            field=models.ForeignKey(related_name='staff_roles', on_delete=models.deletion.SET_NULL, blank=True, to='taxonomy.Programme', help_text=b'', null=True),
        ),
        migrations.AlterField(
            model_name='staffpagerole',
            name='school',
            field=models.ForeignKey(related_name='staff_roles', on_delete=models.deletion.SET_NULL, blank=True, to='taxonomy.School', help_text=b'', null=True),
        ),
    ]
