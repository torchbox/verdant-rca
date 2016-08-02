# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations, models


# Values found in school field that are actually areas
SCHOOLS_THAT_ARE_ACTUALLY_AREAS = ['innovationrca', 'helenhamlyn', 'rectorate']


def migrate_staff_revisions(apps, schema_editor):
    """
    Run the same operation that was done in 0026_auto_20160701_1417
    but now against staff revisions
    """
    Programme = apps.get_model('taxonomy.Programme')
    School = apps.get_model('taxonomy.School')
    Area = apps.get_model('taxonomy.Area')
    StaffPage = apps.get_model('rca.StaffPage')

    for staff_page in StaffPage.objects.all().iterator():
        for revision in staff_page.revisions.all().iterator():
            content = json.loads(revision.content_json)
            changed = False

            # Roles
            if 'roles' in content:
                for role in content['roles']:
                    # Remap some schools to areas
                    if 'school' in role:
                        if role['school'] in SCHOOLS_THAT_ARE_ACTUALLY_AREAS:
                            role['area'] = role['school']
                            role['school'] = None

                    if 'school' in role and not isinstance(role['school'], int):
                        if role['school']:
                            role['school'] =  School.objects.get(slug=role['school']).id
                        else:
                            role['school'] = None

                        changed = True

                    if 'programme' in role and not isinstance(role['programme'], int):
                        # Remap
                        if role['programme'] == 'drawingstudio':
                            # Only affects one page, live version has programme unset
                            role['programme'] = ''

                        if role['programme']:
                            role['programme'] =  Programme.objects.get(slug=role['programme']).id
                        else:
                            role['programme'] = None

                        changed = True

                    if 'area' in role and not isinstance(role['area'], int):
                        if role['area']:
                            # Remap
                            if role['area'] == 'research':
                                role['area'] = 'research-knowledgeexchange'

                            role['area'] =  Area.objects.get(slug=role['area']).id
                        else:
                            role['area'] = None

                        changed = True

            # NOTE: The school field actually points to areas
            if 'school' in content:
                if content['school']:
                    # Remap
                    if content['school'] == 'schoolofcommunications':
                        content['school'] = 'schoolofcommunication'

                    content['area'] = Area.objects.get(slug=content['school']).id
                else:
                    content['area'] = None

                changed = True

            if changed:
                revision.content_json = json.dumps(content, cls=DjangoJSONEncoder)
                revision.save(update_fields=['content_json'])


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0028_auto_20160701_1714'),
    ]

    operations = [
        migrations.RunPython(migrate_staff_revisions, do_nothing),
    ]
