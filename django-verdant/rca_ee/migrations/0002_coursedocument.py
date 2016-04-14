# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtaildocs', '0003_add_verbose_names'),
        ('rca_ee', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseDocument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('for_course', models.TextField(help_text=b'The name of the course for which this document is valid. It will only be shown for registrations on this course. Please enter the name of the course exactly as it appears in the selection form below.')),
                ('document', models.ForeignKey(related_name='+', to='wagtaildocs.Document')),
                ('page', modelcluster.fields.ParentalKey(related_name='documents', to='rca_ee.FormPage')),
            ],
        ),
    ]
