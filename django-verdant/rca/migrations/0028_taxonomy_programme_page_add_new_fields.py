# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0027_taxonomy_school_page_remove_old_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='programmepage',
            name='school_new',
            field=models.ForeignKey(related_name='programme_pages', on_delete=django.db.models.deletion.SET_NULL, verbose_name=b'School', to='taxonomy.School', help_text=b'', null=True),
        ),
        migrations.AddField(
            model_name='programmepageprogramme',
            name='programme_new',
            field=models.ForeignKey(related_name='programme_pages', on_delete=django.db.models.deletion.SET_NULL, verbose_name=b'Programme', to='taxonomy.Programme', help_text=b'', null=True),
        ),
    ]
