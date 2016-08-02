# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations, models


ALL_PROGRAMMES = tuple(sorted([
    ('fashionwomenswear', 'Fashion Womenswear'),
    ('textiles', 'Textiles'),
    ('ceramicsglass', 'Ceramics & Glass'),
    ('sculpture', 'Sculpture'),
    ('designproducts', 'Design Products'),
    ('industrialdesignengineering', 'Industrial Design Engineering'),
    ('goldsmithingsilversmithingmetalworkjewellery', 'Goldsmithing, Silversmithing, Metalwork & Jewellery'),
    ('jewelleryandmetal', 'Jewellery & Metal'),
    ('visualcommunication', 'Visual Communication'),
    ('designinteractions', 'Design Interactions'),
    ('innovationdesignengineering', 'Innovation Design Engineering'),
    ('historyofdesign', 'History of Design'),
    ('fashionmenswear', 'Fashion Menswear'),
    ('printmaking', 'Printmaking'),
    ('print', 'Print'),
    ('globalinnovationdesign', 'Global Innovation Design'),
    ('architecture', 'Architecture'),
    ('interiordesign', 'Interior Design'),
    ('drawingstudio', 'Drawing Studio'),
    ('criticalhistoricalstudies', 'Critical & Historical Studies'),
    ('painting', 'Painting'),
    ('photography', 'Photography'),
    ('servicedesign', 'Service Design'),
    ('animation', 'Animation'),
    ('informationexperiencedesign', 'Information Experience Design'),
    ('criticalwritinginartdesign', 'Critical Writing in Art & Design'),
    ('curatingcontemporaryart', 'Curating Contemporary Art'),
    ('conservation', 'Conservation'),
    ('vehicledesign', 'Vehicle Design'),
    ('communicationartdesign', 'Communication Art & Design'),
    ('contemporaryartpractice', 'Contemporary Art Practice'),
    ('mres-rca-humanities-pathway', 'MRes RCA: Humanities Pathway'),
    ('mres-rca-design-pathway', 'MRes RCA: Design Pathway'),
    ('mres-rca-communication-design-pathway', 'MRes RCA: Communication Design Pathway'),
    ('mres-rca-fine-art-pathway', 'MRes RCA: Fine Art Pathway'),
    ('mres-healthcare-and-design', 'MRes: Healthcare & Design'),
    ('mres-rca-architecture-pathway', 'MRes RCA: Architecture Pathway'),
], key=lambda programme: programme[0]))  # ALL_PROGRAMMES needs to be in alphabetical order (#504 Issue 1)


def migrate_student_revisions(apps, schema_editor):
    """
    Run the same operation that was done in 0026_populate_student_programme_fields
    but now against student revisions
    """
    Programme = apps.get_model('taxonomy.Programme')
    School = apps.get_model('taxonomy.School')
    NewStudentPage = apps.get_model('rca.NewStudentPage')

    all_programmes = dict(ALL_PROGRAMMES)

    def get_or_create_programme(programme_slug, school_slug):
        try:
            return Programme.objects.get(
                slug=programme_slug,
            )
        except Programme.DoesNotExist:
            school = School.objects.get(slug=school_slug)

            return Programme.objects.create(
                slug=programme_slug,
                school=school,
                display_name=all_programmes.get(programme_slug) or programme_slug,
            )

    for student_page in NewStudentPage.objects.all().iterator():
        for revision in student_page.revisions.all().iterator():
            content = json.loads(revision.content_json)
            changed = False

            if 'ma_programme' in content and not isinstance(content['ma_programme'], int):
                if content['ma_programme']:
                    content['ma_programme'] = get_or_create_programme(
                        content['ma_programme'],
                        content['ma_school']
                    ).id
                else:
                    content['ma_programme'] = None

                changed = True

            if 'mphil_programme' in content and not isinstance(content['mphil_programme'], int):
                if content['mphil_programme']:
                    content['mphil_programme'] = get_or_create_programme(
                        content['mphil_programme'],
                        content['mphil_school']
                    ).id
                else:
                    content['mphil_programme'] = None

                changed = True

            if 'phd_programme' in content and not isinstance(content['phd_programme'], int):
                if content['phd_programme']:
                    content['phd_programme'] = get_or_create_programme(
                        content['phd_programme'],
                        content['phd_school']
                    ).id
                else:
                    content['phd_programme'] = None

                changed = True

            if changed:
                revision.content_json = json.dumps(content, cls=DjangoJSONEncoder)
                revision.save(update_fields=['content_json'])


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0028_auto_20160630_1536'),
    ]

    operations = [
        migrations.RunPython(migrate_student_revisions, do_nothing),
    ]
