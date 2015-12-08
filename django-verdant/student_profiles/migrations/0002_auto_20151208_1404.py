# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('student_profiles', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentprofilessettings',
            name='show_pages_enabled',
            field=models.BooleanField(default=True, help_text=b'Determine whether show pages and postcard upload are enabled.'),
        ),
        migrations.AlterField(
            model_name='studentprofilessettings',
            name='new_student_page_index',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, default=6201, verbose_name=b'Student pages', to='wagtailcore.Page', help_text=b'New student pages will be added as children of this page.'),
        ),
        migrations.AlterField(
            model_name='studentprofilessettings',
            name='rca_now_index',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, default=36, verbose_name=b'RCA Now pages', to='wagtailcore.Page', help_text=b'New RCA Now pages will be added as children of this page.'),
        ),
    ]
