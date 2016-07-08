# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations, models


def migrate_rca_now_taxonomy(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    Area = apps.get_model('taxonomy.Area')
    RcaNowPage = apps.get_model('rca.RcaNowPage')
    RcaNowPageArea = apps.get_model('rca.RcaNowPageArea')

    for rca_now_page in RcaNowPage.objects.all().iterator():
        update_fields = []

        if rca_now_page.school:
            # Remap
            if rca_now_page.school == 'schoolofarchitecturedesign':
                rca_now_page.school = 'schoolofarchitecture'

            if rca_now_page.school == 'schoolofcommunications':
                rca_now_page.school = 'schoolofcommunication'

            rca_now_page.school_new = School.objects.get(slug=rca_now_page.school)

            update_fields.append('school_new')

        if rca_now_page.programme:
            rca_now_page.programme_new = Programme.objects.get(slug=rca_now_page.programme)

            update_fields.append('programme_new')

        if update_fields:
            rca_now_page.save(update_fields=update_fields)

    for area in RcaNowPageArea.objects.all().iterator():
        update_fields = []

        if area.area:
            area.area_new = Area.objects.get(slug=area.area)

            update_fields.append('area_new')

        if update_fields:
            area.save(update_fields=update_fields)


def migrate_rca_now_taxonomy_revisions(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    Area = apps.get_model('taxonomy.Area')
    RcaNowPage = apps.get_model('rca.RcaNowPage')

    for rca_now in RcaNowPage.objects.all().iterator():
        for revision in rca_now.revisions.all().iterator():
            content = json.loads(revision.content_json)

            if content['school']:
                # Remap
                if content['school'] == 'schoolofarchitecturedesign':
                    content['school'] = 'schoolofarchitecture'

                if content['school'] == 'schoolofcommunications':
                    content['school'] = 'schoolofcommunication'

                content['school'] = School.objects.get(slug=content['school']).id
            else:
                content['school'] = None

            if content['programme']:
                content['programme'] = Programme.objects.get(slug=content['programme']).id
            else:
                content['programme'] = None

            if 'areas' in content:
                for area in content['areas']:
                    if 'area' in area and not isinstance(area['area'], int):
                        if area['area']:
                            # Remap
                            if area['area'] in ['research', 'knowledgeexchange']:
                                area['area'] = 'research-knowledgeexchange'

                            area['area'] = Area.objects.get(slug=area['area']).id
                        else:
                            area['area'] = None

            revision.content_json = json.dumps(content, cls=DjangoJSONEncoder)
            revision.save(update_fields=['content_json'])


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0025_taxonomy_rca_now_add_new_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_rca_now_taxonomy, do_nothing),
        migrations.RunPython(migrate_rca_now_taxonomy_revisions, do_nothing),
    ]
