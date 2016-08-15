# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0036_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='programmepage',
            name='school',
            field=models.ForeignKey(related_name='programme_pages', on_delete=django.db.models.deletion.SET_NULL, to='taxonomy.School', help_text=b'', null=True),
        ),
        migrations.AlterField(
            model_name='programmepageprogramme',
            name='programme',
            field=models.ForeignKey(related_name='programme_pages', on_delete=django.db.models.deletion.SET_NULL, to='taxonomy.Programme', help_text=b'', null=True),
        ),
        migrations.AlterField(
            model_name='rcanowpage',
            name='author',
            field=models.CharField(help_text=b"Enter your full name as you'd like it to appear, e.g. Tom Smith. If this post was authored by a group of people, add all names as they are supposed to appear.", max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='schoolpage',
            name='school',
            field=models.ForeignKey(related_name='school_pages', on_delete=django.db.models.deletion.SET_NULL, to='taxonomy.School', help_text=b'', null=True),
        ),
    ]
