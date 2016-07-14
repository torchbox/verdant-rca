# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations, models


def migrate_research_taxonomy(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    ResearchItem = apps.get_model('rca.ResearchItem')

    for research_page in ResearchItem.objects.all().iterator():
        update_fields = []

        if research_page.school and research_page.school not in ['innovationrca', 'helenhamlyn']:
            # Remap
            if research_page.school == 'schoolofarchitecturedesign':
                research_page.school = 'schoolofarchitecture'

            if research_page.school == 'schoolofcommunications':
                research_page.school = 'schoolofcommunication'

            if research_page.school == 'schooloffashiontextiles':
                research_page.school = 'schoolofmaterial'

            research_page.school_new = School.objects.get(slug=research_page.school)

            update_fields.append('school_new')

        if research_page.programme:
            # Remap
            if research_page.programme == 'industrialdesignengineering':
                # See 0026_taxonomy_event_item_migrate_data
                research_page.programme = 'innovationdesignengineering'

            research_page.programme_new = Programme.objects.get(slug=research_page.programme)

            update_fields.append('programme_new')

        if update_fields:
            research_page.save(update_fields=update_fields)


def migrate_research_taxonomy_revisions(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    Area = apps.get_model('taxonomy.Area')
    ResearchItem = apps.get_model('rca.ResearchItem')

    for research in ResearchItem.objects.all().iterator():
        for revision in research.revisions.all().iterator():
            content = json.loads(revision.content_json)

            if content['school'] and content['school'] not in ['innovationrca', 'helenhamlyn']:
                # Remap
                if content['school'] == 'schoolofarchitecturedesign':
                    content['school'] = 'schoolofarchitecture'

                if content['school'] == 'schoolofcommunications':
                    content['school'] = 'schoolofcommunication'

                if content['school'] == 'schooloffashiontextiles':
                    content['school'] = 'schoolofmaterial'

                content['school'] = School.objects.get(slug=content['school']).id
            else:
                content['school'] = None

            if content['programme']:
                # Remap
                if content['programme'] == 'industrialdesignengineering':
                    # See 0026_taxonomy_event_item_migrate_data
                    content['programme'] = 'innovationdesignengineering'


                content['programme'] = Programme.objects.get(slug=content['programme']).id
            else:
                content['programme'] = None

            revision.content_json = json.dumps(content, cls=DjangoJSONEncoder)
            revision.save(update_fields=['content_json'])


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0025_taxonomy_research_add_new_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_research_taxonomy, do_nothing),
        migrations.RunPython(migrate_research_taxonomy_revisions, do_nothing),
    ]
