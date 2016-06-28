# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def populate_new_programme_fields(apps, schema_editor):
    Programme = apps.get_model('taxonomy.Programme')
    ShowIndexPageProgramme = apps.get_model('rca_show.ShowIndexPageProgramme')
    ShowIndexProgrammeIntro = apps.get_model('rca_show.ShowIndexProgrammeIntro')

    for sip_programme in ShowIndexPageProgramme.objects.all().iterator():
        sip_programme.programme_new = Programme.objects.get(slug=sip_programme.programme)
        sip_programme.save(update_fields=['programme_new'])

    for sip_programme_intro in ShowIndexProgrammeIntro.objects.all().iterator():
        # HACK: Fix incorrect programme (doesnt exist in 2015)
        if sip_programme_intro.programme == 'goldsmithingsilversmithingmetalworkjewellery' and sip_programme_intro.page.year == '2015':
            sip_programme_intro.programme = 'jewelleryandmetal'

        sip_programme_intro.programme_new = Programme.objects.get(slug=sip_programme_intro.programme)
        sip_programme_intro.save(update_fields=['programme_new'])


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration


class Migration(migrations.Migration):

    dependencies = [
        ('rca_show', '0005_auto_20160628_1549'),
    ]

    operations = [
        migrations.RunPython(populate_new_programme_fields, do_nothing),
    ]
