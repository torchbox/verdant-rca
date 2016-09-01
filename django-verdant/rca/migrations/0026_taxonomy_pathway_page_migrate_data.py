# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations, models


def migrate_pathway_page_taxonomy(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    PathwayPage = apps.get_model('rca.PathwayPage')

    for pathway_page in PathwayPage.objects.all().iterator():
        update_fields = []

        if pathway_page.related_school and pathway_page.related_school:
            pathway_page.related_school_new = School.objects.get(slug=pathway_page.related_school)

            update_fields.append('related_school_new')

        if pathway_page.related_programme:
            pathway_page.related_programme_new = Programme.objects.get(slug=pathway_page.related_programme)

            update_fields.append('related_programme_new')

        if update_fields:
            pathway_page.save(update_fields=update_fields)


def migrate_pathway_page_taxonomy_revisions(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    Area = apps.get_model('taxonomy.Area')
    PathwayPage = apps.get_model('rca.PathwayPage')

    for pathway_page in PathwayPage.objects.all().iterator():
        for revision in pathway_page.revisions.all().iterator():
            content = json.loads(revision.content_json)

            if content['related_school'] and content['related_school']:
                content['related_school'] = School.objects.get(slug=content['related_school']).id
            else:
                content['related_school'] = None

            if content['related_programme']:
                content['related_programme'] = Programme.objects.get(slug=content['related_programme']).id
            else:
                content['related_programme'] = None

            revision.content_json = json.dumps(content, cls=DjangoJSONEncoder)
            revision.save(update_fields=['content_json'])


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0025_taxonomy_pathway_page_add_new_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_pathway_page_taxonomy, do_nothing),
        migrations.RunPython(migrate_pathway_page_taxonomy_revisions, do_nothing),
    ]
