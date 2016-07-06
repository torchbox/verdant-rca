# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


AREA_CHOICES = (
    ('administration', 'Administration'),
    ('alumnirca', 'AlumniRCA'),
    ('communicationsmarketing', 'Communications & Marketing'),
    ('development', 'Development'),
    ('drawingstudio', 'Drawing Studio'),
    ('executiveeducation', 'Executive Education'),
    ('fuelrca', 'Fuel RCA'),
    ('helenhamlyn', 'The Helen Hamlyn Centre for Design'),
    ('informationlearningtechnicalservices', 'Information, Learning & Technical Services'),
    ('innovationrca', 'InnovationRCA'),
    ('reachoutrca', 'ReachOutRCA'),
    ('rectorate', 'Rectorate'),
    ('research-knowledgeexchange', "Research, Knowledge Exchange & Innovation"),
    ('schoolofarchitecture', 'School of Architecture'),
    ('schoolofcommunication', 'School of Communication'),
    ('schoolofdesign', 'School of Design'),
    ('schooloffineart', 'School of Fine Art'),
    ('schoolofhumanities', 'School of Humanities'),
    ('schoolofmaterial', 'School of Material'),
    ('showrca', 'Show RCA'),
    ('support', 'Support'),
    ('sustainrca', 'SustainRCA'),
    ('performance', "Performance"),
    ('moving-image', "Moving image"),
)


SCHOOL_CHOICES = (
    ('schoolofarchitecture', 'School of Architecture'),
    ('schoolofcommunication', 'School of Communication'),
    ('schoolofdesign', 'School of Design'),
    ('schooloffineart', 'School of Fine Art'),
    ('schoolofhumanities', 'School of Humanities'),
    ('schoolofmaterial', 'School of Material'),
    ('helenhamlyn', 'The Helen Hamlyn Centre for Design'),
    ('rectorate', 'Rectorate'),
    ('innovationrca', 'InnovationRCA'),
)

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


SCHOOL_PROGRAMME_MAP = {
    '2017': {
        'schoolofarchitecture': ['architecture', 'interiordesign', 'mres-rca-architecture-pathway'],
        'schoolofcommunication': ['animation', 'informationexperiencedesign', 'visualcommunication', 'mres-rca-communication-design-pathway'],
        'schoolofdesign': ['designinteractions', 'designproducts', 'globalinnovationdesign', 'innovationdesignengineering', 'servicedesign', 'vehicledesign', 'mres-rca-design-pathway', 'mres-healthcare-and-design'],
        'schooloffineart': ['painting', 'photography', 'print', 'sculpture', 'contemporaryartpractice', 'mres-rca-fine-art-pathway'],
        'schoolofhumanities': ['criticalhistoricalstudies', 'criticalwritinginartdesign', 'curatingcontemporaryart', 'historyofdesign', 'mres-rca-humanities-pathway'],
        'schoolofmaterial': ['ceramicsglass', 'jewelleryandmetal', 'fashionmenswear', 'fashionwomenswear', 'textiles'],
    },
    '2016': {
        'schoolofarchitecture': ['architecture', 'interiordesign'],
        'schoolofcommunication': ['animation', 'informationexperiencedesign', 'visualcommunication'],
        'schoolofdesign': ['designinteractions', 'designproducts', 'globalinnovationdesign', 'innovationdesignengineering', 'servicedesign', 'vehicledesign'],
        'schooloffineart': ['painting', 'photography', 'print', 'sculpture', 'contemporaryartpractice'],
        'schoolofhumanities': ['criticalhistoricalstudies', 'criticalwritinginartdesign', 'curatingcontemporaryart', 'historyofdesign'],
        'schoolofmaterial': ['ceramicsglass', 'jewelleryandmetal', 'fashionmenswear', 'fashionwomenswear', 'textiles'],
    },
    '2015': {
        'schoolofarchitecture': ['architecture', 'interiordesign'],
        'schoolofcommunication': ['animation', 'informationexperiencedesign', 'visualcommunication'],
        'schoolofdesign': ['designinteractions', 'designproducts', 'globalinnovationdesign', 'innovationdesignengineering', 'servicedesign', 'vehicledesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['criticalhistoricalstudies', 'criticalwritinginartdesign', 'curatingcontemporaryart', 'historyofdesign'],
        'schoolofmaterial': ['ceramicsglass', 'jewelleryandmetal', 'fashionmenswear', 'fashionwomenswear', 'textiles'],
    },
    '2014': {
        'schoolofarchitecture': ['architecture', 'interiordesign'],
        'schoolofcommunication': ['animation', 'informationexperiencedesign', 'visualcommunication'],
        'schoolofdesign': ['designinteractions', 'designproducts', 'globalinnovationdesign', 'innovationdesignengineering', 'servicedesign', 'vehicledesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['criticalhistoricalstudies', 'criticalwritinginartdesign', 'curatingcontemporaryart', 'historyofdesign'],
        'schoolofmaterial': ['ceramicsglass', 'goldsmithingsilversmithingmetalworkjewellery', 'jewelleryandmetal', 'fashionmenswear', 'fashionwomenswear', 'textiles'],
    },
    '2013': {
        'schoolofarchitecture': ['architecture'],
        'schoolofcommunication': ['animation', 'visualcommunication'],
        'schoolofdesign': ['designinteractions', 'designproducts', 'innovationdesignengineering', 'servicedesign', 'vehicledesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['criticalhistoricalstudies', 'criticalwritinginartdesign', 'curatingcontemporaryart', 'historyofdesign'],
        'schoolofmaterial': ['ceramicsglass', 'goldsmithingsilversmithingmetalworkjewellery', 'fashionmenswear', 'fashionwomenswear', 'textiles'],
    },
    '2012': {
        'schoolofarchitecture': ['architecture'],
        'schoolofcommunication': ['animation', 'visualcommunication'],
        'schoolofdesign': ['designinteractions', 'designproducts', 'innovationdesignengineering', 'vehicledesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['criticalhistoricalstudies', 'criticalwritinginartdesign', 'curatingcontemporaryart', 'historyofdesign'],
        'schoolofmaterial': ['ceramicsglass', 'goldsmithingsilversmithingmetalworkjewellery', 'fashionmenswear', 'fashionwomenswear', 'textiles'],
    },
    '2011': {
        'schoolofarchitecture': ['architecture'],
        'schoolofcommunication': ['animation', 'communicationartdesign'],
        'schoolofdesign': ['designinteractions', 'designproducts', 'innovationdesignengineering', 'vehicledesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['criticalhistoricalstudies', 'criticalwritinginartdesign', 'curatingcontemporaryart', 'historyofdesign'],
        'schoolofmaterial': ['ceramicsglass', 'goldsmithingsilversmithingmetalworkjewellery', 'fashionmenswear', 'fashionwomenswear', 'textiles'],
    },
    '2010': {
        'schoolofarchitecture': ['architecture'],
        'schoolofcommunication': ['animation', 'communicationartdesign'],
        'schoolofdesign': ['designinteractions', 'designproducts', 'innovationdesignengineering', 'vehicledesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['criticalhistoricalstudies', 'criticalwritinginartdesign', 'curatingcontemporaryart', 'historyofdesign'],
        'schoolofmaterial': ['ceramicsglass', 'goldsmithingsilversmithingmetalworkjewellery', 'fashionmenswear', 'fashionwomenswear', 'textiles'],
    },
    '2009': {
        'schoolofcommunication': ['animation', 'communicationartdesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['conservation', 'criticalhistoricalstudies', 'curatingcontemporaryart', 'historyofdesign'],
    },
    '2008': {
        'schoolofcommunication': ['animation', 'communicationartdesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['conservation', 'criticalhistoricalstudies', 'curatingcontemporaryart', 'historyofdesign'],
    },
    '2007': {
        'schoolofcommunication': ['animation', 'communicationartdesign'],
        'schooloffineart': ['painting', 'photography', 'printmaking', 'sculpture'],
        'schoolofhumanities': ['conservation', 'criticalhistoricalstudies', 'curatingcontemporaryart', 'historyofdesign'],
    },
}


def create_initial_areas(apps, schema_editor):
    Area = apps.get_model('taxonomy.Area')

    for slug, display_name in AREA_CHOICES:
        Area.objects.create(
            slug=slug,
            display_name=display_name,
        )


def create_initial_schools_and_programmes(apps, schema_editor):
    School = apps.get_model('taxonomy.School')
    Programme = apps.get_model('taxonomy.Programme')

    school_choices = dict(SCHOOL_CHOICES)
    programme_choices = dict(ALL_PROGRAMMES)

    for year, schools in SCHOOL_PROGRAMME_MAP.items():
        for school_slug, programmes in schools.items():
            school_display_name = school_choices[school_slug]

            school = School.objects.create(
                year=year,
                slug=school_slug,
                display_name=school_display_name,
            )

            for programme_slug in programmes:
                programme_display_name = programme_choices[programme_slug]

                Programme.objects.create(
                    school=school,
                    slug=programme_slug,
                    display_name=programme_display_name,
                )


def do_nothing(apps, schema_editor):
    pass  # Allows us to reverse this migration


class Migration(migrations.Migration):

    dependencies = [
        ('taxonomy', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_areas, do_nothing),
        migrations.RunPython(create_initial_schools_and_programmes, do_nothing),
    ]
