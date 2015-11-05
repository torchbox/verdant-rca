# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0012_auto_20151007_1535'),
    ]

    operations = [
        migrations.AlterField(
            model_name='staffpage',
            name='school',
            field=models.CharField(blank=True, help_text=b'Please complete this field for academic and administrative staff only', max_length=255, verbose_name=b'Area', choices=[(b'administration', b'Administration'), (b'alumnirca', b'AlumniRCA'), (b'communicationsmarketing', b'Communications & Marketing'), (b'development', b'Development'), (b'drawingstudio', b'Drawing Studio'), (b'executiveeducation', b'Executive Education'), (b'fuelrca', b'Fuel RCA'), (b'helenhamlyn', b'The Helen Hamlyn Centre for Design'), (b'informationlearningtechnicalservices', b'Information, Learning & Technical Services'), (b'innovationrca', b'InnovationRCA'), (b'reachoutrca', b'ReachOutRCA'), (b'rectorate', b'Rectorate'), (b'research-knowledgeexchange', b'Research, Knowledge Exchange & Innovation'), (b'schoolofarchitecture', b'School of Architecture'), (b'schoolofcommunication', b'School of Communication'), (b'schoolofdesign', b'School of Design'), (b'schooloffineart', b'School of Fine Art'), (b'schoolofhumanities', b'School of Humanities'), (b'schoolofmaterial', b'School of Material'), (b'showrca', b'Show RCA'), (b'support', b'Support'), (b'sustainrca', b'SustainRCA')]),
        ),
    ]
