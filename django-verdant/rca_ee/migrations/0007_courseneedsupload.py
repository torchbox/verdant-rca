# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('rca_ee', '0006_auto_20160413_1115'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseNeedsUpload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('for_course', models.TextField(help_text=b'The name of the course for which a portfolio upload is necessary before registering interest. Please enter the name of the course exactly as it appears in the selection form below.')),
                ('page', modelcluster.fields.ParentalKey(related_name='portfolio_necessary', to='rca_ee.BookingFormPage')),
            ],
        ),
    ]
