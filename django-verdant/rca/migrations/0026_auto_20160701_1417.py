# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


# Values found in school field that are actually areas
SCHOOLS_THAT_ARE_ACTUALLY_AREAS = ['innovationrca', 'helenhamlyn', 'rectorate']


def populate_new_staff_taxonomy_fields(apps, schema_editor):
    Programme = apps.get_model('taxonomy.Programme')
    School = apps.get_model('taxonomy.School')
    Area = apps.get_model('taxonomy.Area')
    StaffPageRole = apps.get_model('rca.StaffPageRole')
    StaffPage = apps.get_model('rca.StaffPage')

    for staff_page_role in StaffPageRole.objects.all().iterator():
        update_fields = []

        # Remap some schools to areas
        if staff_page_role.school in SCHOOLS_THAT_ARE_ACTUALLY_AREAS:
            staff_page_role.area = staff_page_role.school
            staff_page_role.school = ''

        if staff_page_role.school:
            staff_page_role.school_new = School.objects.get(slug=staff_page_role.school)
            update_fields.append('school_new')

        if staff_page_role.programme:
            staff_page_role.programme_new = Programme.objects.get(slug=staff_page_role.programme)
            update_fields.append('programme_new')

        if staff_page_role.area:
            staff_page_role.area_new = Area.objects.get(slug=staff_page_role.area)
            update_fields.append('area_new')

        if update_fields:
            staff_page_role.save(update_fields=update_fields)

    for staff_page in StaffPage.objects.all().iterator():
        update_fields = []

        # NOTE: The school field actually points to areas
        if staff_page.school:
            staff_page.area = Area.objects.get(slug=staff_page.school)
            staff_page.save(update_fields=['area'])


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration



class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0025_auto_20160701_1415'),
    ]

    operations = [
        migrations.RunPython(populate_new_staff_taxonomy_fields, do_nothing),
    ]
