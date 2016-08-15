# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations, models


def migrate_event_item_taxonomy(apps, schema_editor):
    Area = apps.get_model('taxonomy.Area')
    EventItem = apps.get_model('rca.EventItem')

    for event_item in EventItem.objects.all().iterator():
        update_fields = []

        if event_item.area:
            event_item.area_new = Area.objects.get(slug=event_item.area)

            update_fields.append('area_new')

        if update_fields:
            event_item.save(update_fields=update_fields)


def migrate_event_item_taxonomy_revisions(apps, schema_editor):
    Area = apps.get_model('taxonomy.Area')
    EventItem = apps.get_model('rca.EventItem')

    for event_item in EventItem.objects.all().iterator():
        for revision in event_item.revisions.all().iterator():
            content = json.loads(revision.content_json)

            if content['area']:
                # Remap
                if content['area'] in ['research', 'knowledgeexchange']:
                    content['area'] = 'research-knowledgeexchange'

                content['area'] = Area.objects.get(slug=content['area']).id
            else:
                content['area'] = None

            revision.content_json = json.dumps(content, cls=DjangoJSONEncoder)
            revision.save(update_fields=['content_json'])


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0033_taxonomy_event_item_add_new_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_event_item_taxonomy, do_nothing),
        migrations.RunPython(migrate_event_item_taxonomy_revisions, do_nothing),
    ]
