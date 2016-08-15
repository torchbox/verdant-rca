# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0026_taxonomy_research_innovation_page_migrate_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='researchinnovationpage',
            name='news_carousel_area',
        ),
        migrations.RenameField(
            model_name='researchinnovationpage',
            old_name='news_carousel_area_new',
            new_name='news_carousel_area',
        ),
    ]
