# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0020_add_index_on_page_first_published_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentProfilesSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('new_student_page_index', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, default=6201, verbose_name=b'Index for new student pages', to='wagtailcore.Page', help_text=b'New student pages will be added as children of this page.')),
                ('rca_now_index', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, default=36, verbose_name=b'Index for new RCA Now pages', to='wagtailcore.Page', help_text=b'New RCA Now pages will be added as children of this page.')),
                ('site', models.OneToOneField(editable=False, to='wagtailcore.Site')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
