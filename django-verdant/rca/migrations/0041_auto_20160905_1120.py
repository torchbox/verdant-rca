# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import wagtail.wagtailimages.models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0040_rcaimage_collection'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rcarendition',
            name='file',
            field=models.ImageField(height_field='height', width_field='width', upload_to=wagtail.wagtailimages.models.get_rendition_upload_to),
        ),
    ]
