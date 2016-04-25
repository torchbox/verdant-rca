# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rca_ee', '0008_auto_20160413_1343'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookingformpage',
            name='terms_and_conditions',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='wagtaildocs.Document', help_text=b'This document will be shown as the Terms and Conditions document.', null=True, verbose_name=b'Terms and Conditions'),
        ),
        migrations.AlterField(
            model_name='formpage',
            name='terms_and_conditions',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='wagtaildocs.Document', help_text=b'This document will be shown as the Terms and Conditions document.', null=True, verbose_name=b'Terms and Conditions'),
        ),
    ]
