# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import wagtail.wagtailcore.models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0028_merge'),
        ('rca', '0039_auto_20160905_1118'),
    ]

    operations = [
        migrations.AddField(
            model_name='rcaimage',
            name='collection',
            field=models.ForeignKey(related_name='+', default=wagtail.wagtailcore.models.get_root_collection_id, verbose_name='collection', to='wagtailcore.Collection'),
        ),
    ]
