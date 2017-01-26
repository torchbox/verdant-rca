# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations, models


PROGRAMMES_MAPPING = {
    79: 15,  # Printmaking => Print
    92: 2,  # Goldsmithing, Silversmithing, Metalwork & Jewellery => Jewellery & Metal
    143: 11,  # Communication Art & Design => Visual Communication
    217: 22,  # Industrial Design Engineering => Innovation Design Engineering
}


def migrate_renamed_programmes(apps, schema_editor):
    # Research items
    ResearchItem = apps.get_model('rca.ResearchItem')
    research_items = ResearchItem.objects.filter(programme__in=PROGRAMMES_MAPPING.keys())
    for research_item in research_items.iterator():
        research_item.programme_id = PROGRAMMES_MAPPING[research_item.programme_id]
        research_item.save(update_fields=['programme_id'])

    # Students
    NewStudentPage = apps.get_model('rca.NewStudentPage')

    ma_students = NewStudentPage.objects.filter(ma_programme_id__in=PROGRAMMES_MAPPING.keys())
    for student in ma_students.iterator():
        student.ma_programme_id = PROGRAMMES_MAPPING[student.ma_programme_id]
        student.save(update_fields=['ma_programme_id'])

    mphil_students = NewStudentPage.objects.filter(mphil_programme_id__in=PROGRAMMES_MAPPING.keys())
    for student in mphil_students.iterator():
        student.mphil_programme_id = PROGRAMMES_MAPPING[student.mphil_programme_id]
        student.save(update_fields=['mphil_programme_id'])

    phd_students = NewStudentPage.objects.filter(phd_programme_id__in=PROGRAMMES_MAPPING.keys())
    for student in phd_students.iterator():
        student.phd_programme_id = PROGRAMMES_MAPPING[student.phd_programme_id]
        student.save(update_fields=['phd_programme_id'])

    # News items
    NewsItemRelatedProgramme = apps.get_model('rca.NewsItemRelatedProgramme')
    related_programmes = NewsItemRelatedProgramme.objects.filter(programme__in=PROGRAMMES_MAPPING.keys())
    for related_programme in related_programmes.iterator():
        related_programme.programme_id = PROGRAMMES_MAPPING[related_programme.programme_id]
        related_programme.save(update_fields=['programme_id'])

    # Event items
    EventItemRelatedProgramme = apps.get_model('rca.EventItemRelatedProgramme')
    related_programmes = EventItemRelatedProgramme.objects.filter(programme__in=PROGRAMMES_MAPPING.keys())
    for related_programme in related_programmes.iterator():
        related_programme.programme_id = PROGRAMMES_MAPPING[related_programme.programme_id]
        related_programme.save(update_fields=['programme_id'])

    # Staff
    StaffPageRole = apps.get_model('rca.StaffPageRole')
    roles = StaffPageRole.objects.filter(programme__in=PROGRAMMES_MAPPING.keys())
    for role in roles.iterator():
        role.programme_id = PROGRAMMES_MAPPING[role.programme_id]
        role.save(update_fields=['programme_id'])

    # Note: At the time this was developed there were no relevant pages in
    # live+draft status so we can safely ignore revisions


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0049_merge'),
    ]

    operations = [
        migrations.RunPython(migrate_renamed_programmes, do_nothing),
    ]
