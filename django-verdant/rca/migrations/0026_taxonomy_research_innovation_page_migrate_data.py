# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations, models


def migrate_research_innovation_page_taxonomy(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    Area = apps.get_model('taxonomy.Area')
    ResearchInnovationPage = apps.get_model('rca.ResearchInnovationPage')

    for research_innovation_page in ResearchInnovationPage.objects.all().iterator():
        update_fields = []

        if research_innovation_page.news_carousel_area:
            research_innovation_page.news_carousel_area_new = Area.objects.get(slug=research_innovation_page.news_carousel_area)

            update_fields.append('news_carousel_area_new')

        if update_fields:
            research_innovation_page.save(update_fields=update_fields)


def migrate_research_innovation_page_taxonomy_revisions(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    Area = apps.get_model('taxonomy.Area')
    ResearchInnovationPage = apps.get_model('rca.ResearchInnovationPage')

    for research_innovation_page in ResearchInnovationPage.objects.all().iterator():
        for revision in research_innovation_page.revisions.all().iterator():
            content = json.loads(revision.content_json)

            if content['news_carousel_area']:
                content['news_carousel_area'] = Area.objects.get(slug=content['news_carousel_area']).id
            else:
                content['news_carousel_area'] = None

            revision.content_json = json.dumps(content, cls=DjangoJSONEncoder)
            revision.save(update_fields=['content_json'])


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0025_taxonomy_research_innovation_page_add_new_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_research_innovation_page_taxonomy, do_nothing),
        migrations.RunPython(migrate_research_innovation_page_taxonomy_revisions, do_nothing),
    ]
