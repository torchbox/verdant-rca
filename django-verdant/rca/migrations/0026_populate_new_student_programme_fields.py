# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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


def populate_new_student_programme_fields(apps, schema_editor):
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
        update_fields = []

        if student_page.ma_programme:
            student_page.ma_programme_new = get_or_create_programme(
                student_page.ma_programme,
                student_page.ma_school
            )

            update_fields.append('ma_programme_new')

        if student_page.mphil_programme:
            student_page.mphil_programme_new = get_or_create_programme(
                student_page.mphil_programme,
                student_page.mphil_school
            )

            update_fields.append('mphil_programme_new')

        if student_page.phd_programme:
            student_page.phd_programme_new = get_or_create_programme(
                student_page.phd_programme,
                student_page.phd_school
            )

            update_fields.append('phd_programme_new')

        if update_fields:
            student_page.save(update_fields=update_fields)


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0025_auto_20160621_1505'),
    ]

    operations = [
        migrations.RunPython(populate_new_student_programme_fields, do_nothing),
    ]
