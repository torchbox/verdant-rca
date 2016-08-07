# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations, models


def migrate_standard_page_taxonomy(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    Area = apps.get_model('taxonomy.Area')
    StandardPage = apps.get_model('rca.StandardPage')
    StandardIndex = apps.get_model('rca.StandardIndex')

    for standard_page in StandardPage.objects.all().iterator():
        update_fields = []

        if standard_page.related_school:
            if standard_page.related_school in ['helenhamlyn', 'innovationrca']:
                # This is a new field which I created because there were a few standard pages that had areas in their school field
                standard_page.related_area = Area.objects.get(slug=standard_page.related_school)

                update_fields.append('related_area')
            else:
                standard_page.related_school_new = School.objects.get(slug=standard_page.related_school)

                update_fields.append('related_school_new')

        if standard_page.related_programme:
            standard_page.related_programme_new = Programme.objects.get(slug=standard_page.related_programme)

            update_fields.append('related_programme_new')

        if update_fields:
            standard_page.save(update_fields=update_fields)

    for standard_index in StandardIndex.objects.all().iterator():
        update_fields = []

        if standard_index.events_feed_area:
            standard_index.events_feed_area_new = Area.objects.get(slug=standard_index.events_feed_area)

            update_fields.append('events_feed_area_new')

        if standard_index.news_carousel_area:
            standard_index.news_carousel_area_new = Area.objects.get(slug=standard_index.news_carousel_area)

            update_fields.append('news_carousel_area_new')

        if standard_index.staff_feed_source:
            standard_index.staff_feed_source_new = Area.objects.get(slug=standard_index.staff_feed_source)

            update_fields.append('staff_feed_source_new')

        if update_fields:
            standard_index.save(update_fields=update_fields)


def migrate_standard_page_taxonomy_revisions(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    Area = apps.get_model('taxonomy.Area')
    StandardPage = apps.get_model('rca.StandardPage')
    StandardIndex = apps.get_model('rca.StandardIndex')

    for standard_page in StandardPage.objects.all().iterator():
        for revision in standard_page.revisions.all().iterator():
            content = json.loads(revision.content_json)

            if 'related_school' in content and content['related_school']:
                if content['related_school'] in ['helenhamlyn', 'innovationrca']:
                    # This is a new field which I created because there were a few standard pages that had areas in their school field
                    content['related_area'] = Area.objects.get(slug=content['related_school']).id
                else:
                    content['related_school'] = School.objects.get(slug=content['related_school']).id

            else:
                content['related_school'] = None

            if 'related_programme' in content and content['related_programme']:
                content['related_programme'] = Programme.objects.get(slug=content['related_programme']).id
            else:
                content['related_programme'] = None

            revision.content_json = json.dumps(content, cls=DjangoJSONEncoder)
            revision.save(update_fields=['content_json'])

    for standard_index in StandardIndex.objects.all().iterator():
        for revision in standard_index.revisions.all().iterator():
            content = json.loads(revision.content_json)

            if content['events_feed_area']:
                # Remap
                if content['events_feed_area'] == 'research':
                    content['events_feed_area'] = 'research-knowledgeexchange'

                content['events_feed_area'] = Area.objects.get(slug=content['events_feed_area']).id
            else:
                content['events_feed_area'] = None

            if content['news_carousel_area']:
                # Remap
                if content['news_carousel_area'] == 'research':
                    content['news_carousel_area'] = 'research-knowledgeexchange'

                content['news_carousel_area'] = Area.objects.get(slug=content['news_carousel_area']).id
            else:
                content['news_carousel_area'] = None

            if 'staff_feed_source' in content and content['staff_feed_source']:
                content['staff_feed_source'] = Area.objects.get(slug=content['staff_feed_source']).id
            else:
                content['staff_feed_source'] = None

            revision.content_json = json.dumps(content, cls=DjangoJSONEncoder)
            revision.save(update_fields=['content_json'])


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0025_taxonomy_standard_page_add_new_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_standard_page_taxonomy, do_nothing),
        migrations.RunPython(migrate_standard_page_taxonomy_revisions, do_nothing),
    ]
