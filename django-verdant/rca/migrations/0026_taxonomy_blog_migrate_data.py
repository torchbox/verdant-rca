# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations, models


def migrate_blog_taxonomy(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    Area = apps.get_model('taxonomy.Area')
    RcaBlogPage = apps.get_model('rca.RcaBlogPage')
    RcaBlogPageArea = apps.get_model('rca.RcaBlogPageArea')

    for blog_page in RcaBlogPage.objects.all().iterator():
        update_fields = []

        if blog_page.school and blog_page.school != 'innovationrca':
            # Remap
            if blog_page.school == 'schoolofarchitecturedesign':
                blog_page.school = 'schoolofarchitecture'

            if blog_page.school == 'schoolofcommunications':
                blog_page.school = 'schoolofcommunication'

            blog_page.school_new = School.objects.get(slug=blog_page.school)

            update_fields.append('school_new')

        if blog_page.programme:
            blog_page.programme_new = Programme.objects.get(slug=blog_page.programme)

            update_fields.append('programme_new')

        if update_fields:
            blog_page.save(update_fields=update_fields)

    for area in RcaBlogPageArea.objects.all().iterator():
        update_fields = []

        if area.area:
            area.area_new = Area.objects.get(slug=area.area)

            update_fields.append('area_new')

        if update_fields:
            area.save(update_fields=update_fields)


def migrate_blog_taxonomy_revisions(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')
    Area = apps.get_model('taxonomy.Area')
    RcaBlogPage = apps.get_model('rca.RcaBlogPage')

    for blog in RcaBlogPage.objects.all().iterator():
        for revision in blog.revisions.all().iterator():
            content = json.loads(revision.content_json)

            if content['school'] and content['school'] != 'innovationrca':
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
        ('rca', '0025_taxonomy_blog_add_new_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_blog_taxonomy, do_nothing),
        migrations.RunPython(migrate_blog_taxonomy_revisions, do_nothing),
    ]
