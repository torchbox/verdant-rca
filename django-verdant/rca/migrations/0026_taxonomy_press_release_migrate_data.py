# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations, models


def migrate_press_release_taxonomy(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    Area = apps.get_model('taxonomy.Area')
    PressReleaseRelatedProgramme = apps.get_model('rca.PressReleaseRelatedProgramme')
    PressReleaseRelatedSchool = apps.get_model('rca.PressReleaseRelatedSchool')
    PressReleaseArea = apps.get_model('rca.PressReleaseArea')

    for related_programme in PressReleaseRelatedProgramme.objects.all().iterator():
        update_fields = []

        if related_programme.programme:
            related_programme.programme_new = Programme.objects.get(slug=related_programme.programme)

            update_fields.append('programme_new')

        if update_fields:
            related_programme.save(update_fields=update_fields)

    for related_school in PressReleaseRelatedSchool.objects.all().iterator():
        update_fields = []

        if related_school.school and not related_school.school in ['helenhamlyn', 'innovationrca']:
            # Remap
            if related_school.school == 'schooloffashiontextiles':
                related_school.school = 'schoolofmaterial'

            if related_school.school == 'schoolofappliedart':
                # School of Applied Art contained programmes that are now part
                # of School of Material
                # www.rca.ac.uk/documents/120/1RCA_Annual_Review_2009-10.pdf
                related_school.school = 'schoolofmaterial'

            if related_school.school == 'schoolofarchitecturedesign':
                related_school.school = 'schoolofarchitecture'

            if related_school.school == 'schoolofcommunications':
                related_school.school = 'schoolofcommunication'

            if related_school.school == 'schoolofdesignforproduction':
                related_school.school = 'schoolofdesign'

            related_school.school_new = School.objects.get(slug=related_school.school)

            update_fields.append('school_new')

        if update_fields:
            related_school.save(update_fields=update_fields)

    for area in PressReleaseArea.objects.all().iterator():
        update_fields = []

        if area.area:
            area.area_new = Area.objects.get(slug=area.area)

            update_fields.append('area_new')

        if update_fields:
            area.save(update_fields=update_fields)


def migrate_press_release_taxonomy_revisions(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    Area = apps.get_model('taxonomy.Area')
    PressRelease = apps.get_model('rca.PressRelease')

    for press_release in PressRelease.objects.all().iterator():
        for revision in press_release.revisions.all().iterator():
            content = json.loads(revision.content_json)
            changed = False

            if 'related_programmes' in content:
                for related_programme in content['related_programmes']:
                    if 'programme' in related_programme and not isinstance(related_programme['programme'], int):
                        if related_programme['programme']:
                            related_programme['programme'] = Programme.objects.get(slug=related_programme['programme']).id
                        else:
                            related_programme['programme'] = None

                        changed = True


            if 'related_schools' in content:
                for related_school in content['related_schools']:
                    if 'school' in related_school and not isinstance(related_school['school'], int):
                        if related_school['school'] and related_school['school'] not in ['helenhamlyn', 'innovationrca']:
                            # Remap
                            if related_school['school'] == 'schooloffashiontextiles':
                                related_school['school'] = 'schoolofmaterial'

                            if related_school['school'] == 'schoolofappliedart':
                                # School of Applied Art contained programmes that are now part
                                # of School of Material
                                # www.rca.ac.uk/documents/120/1RCA_Annual_Review_2009-10.pdf
                                related_school['school'] = 'schoolofmaterial'

                            if related_school['school'] == 'schoolofarchitecturedesign':
                                related_school['school'] = 'schoolofarchitecture'

                            if related_school['school'] == 'schoolofcommunications':
                                related_school['school'] = 'schoolofcommunication'

                            if related_school['school'] == 'schoolofdesignforproduction':
                                related_school['school'] = 'schoolofdesign'

                            related_school['school'] = School.objects.get(slug=related_school['school']).id
                        else:
                            related_school['school'] = None

                        changed = True

            if 'areas' in content:
                for area in content['areas']:
                    if 'area' in area and not isinstance(area['area'], int):
                        if area['area']:
                            # # Remap
                            if area['area'] in ['research', 'knowledgeexchange']:
                                area['area'] = 'research-knowledgeexchange'

                            area['area'] = Area.objects.get(slug=area['area']).id
                        else:
                            area['area'] = None

                        changed = True

            if changed:
                revision.content_json = json.dumps(content, cls=DjangoJSONEncoder)
                revision.save(update_fields=['content_json'])


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0025_taxonomy_press_release_add_new_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_press_release_taxonomy, do_nothing),
        migrations.RunPython(migrate_press_release_taxonomy_revisions, do_nothing),
    ]
