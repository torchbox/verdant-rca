# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations, models


def migrate_event_item_taxonomy(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    Area = apps.get_model('taxonomy.Area')
    EventItemRelatedProgramme = apps.get_model('rca.EventItemRelatedProgramme')
    EventItemRelatedSchool = apps.get_model('rca.EventItemRelatedSchool')
    EventItemRelatedArea = apps.get_model('rca.EventItemRelatedArea')

    for related_programme in EventItemRelatedProgramme.objects.all().iterator():
        update_fields = []

        if related_programme.programme:
            # Remap
            if related_programme.programme == 'industrialdesignengineering':
                # The one page with the programme is titled "Innovation Design Engineering Open Day"
                related_programme.programme = 'innovationdesignengineering'

            related_programme.programme_new = Programme.objects.get(slug=related_programme.programme)

            update_fields.append('programme_new')

        if update_fields:
            related_programme.save(update_fields=update_fields)

    for related_school in EventItemRelatedSchool.objects.all().iterator():
        update_fields = []

        if related_school.school and not related_school.school in ['helenhamlyn', 'innovationrca']:
            # Remap
            if related_school.school == 'schooloffashiontextiles':
                related_school.school = 'schoolofmaterial'

            related_school.school_new = School.objects.get(slug=related_school.school)

            update_fields.append('school_new')

        if update_fields:
            related_school.save(update_fields=update_fields)

    for related_area in EventItemRelatedArea.objects.all().iterator():
        update_fields = []

        if related_area.area:
            related_area.area_new = Area.objects.get(slug=related_area.area)

            update_fields.append('area_new')

        if update_fields:
            related_area.save(update_fields=update_fields)


def migrate_event_item_taxonomy_revisions(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    Area = apps.get_model('taxonomy.Area')
    EventItem = apps.get_model('rca.EventItem')

    for event_item in EventItem.objects.all().iterator():
        for revision in event_item.revisions.all().iterator():
            content = json.loads(revision.content_json)
            changed = False

            if 'related_programmes' in content:
                for related_programme in content['related_programmes']:
                    if 'programme' in related_programme and not isinstance(related_programme['programme'], int):
                        if related_programme['programme']:
                            # Remap
                            if related_programme['programme'] == 'industrialdesignengineering':
                                # The one page with the programme is titled "Innovation Design Engineering Open Day"
                                related_programme['programme'] = 'innovationdesignengineering'

                            related_programme['programme'] = Programme.objects.get(slug=related_programme['programme']).id
                        else:
                            related_programme['programme'] = None

                        changed = True


            if 'related_schools' in content:
                for related_school in content['related_schools']:
                    if 'school' in related_school and not isinstance(related_school['school'], int):
                        if related_school['school'] and related_school['school'] not in ['helenhamlyn', 'innovationrca', 'rectorate']:
                            # Remap
                            if related_school['school'] == 'schooloffashiontextiles':
                                related_school['school'] = 'schoolofmaterial'

                            if related_school['school'] == 'schoolofdesignforproduction':
                                related_school['school'] = 'schoolofdesign'

                            related_school['school'] = School.objects.get(slug=related_school['school']).id
                        else:
                            related_school['school'] = None

                        changed = True

            if 'related_areas' in content:
                for related_area in content['related_areas']:
                    if 'area' in related_area and not isinstance(related_area['area'], int):
                        if related_area['area']:
                            # Remap
                            if related_area['area'] in ['research', 'knowledgeexchange']:
                                related_area['area'] = 'research-knowledgeexchange'

                            related_area['area'] = Area.objects.get(slug=related_area['area']).id
                        else:
                            related_area['area'] = None

                        changed = True

            if changed:
                revision.content_json = json.dumps(content, cls=DjangoJSONEncoder)
                revision.save(update_fields=['content_json'])


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0025_taxonomy_event_item_add_new_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_event_item_taxonomy, do_nothing),
        migrations.RunPython(migrate_event_item_taxonomy_revisions, do_nothing),
    ]
