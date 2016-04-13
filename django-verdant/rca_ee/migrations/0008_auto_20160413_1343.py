# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtaildocs', '0003_add_verbose_names'),
        ('rca_ee', '0007_courseneedsupload'),
    ]

    operations = [
        migrations.AddField(
            model_name='bookingformpage',
            name='terms_and_conditions',
            field=models.ForeignKey(blank=True, to='wagtaildocs.Document', help_text=b'This document will be shown as the Terms and Conditions document.', null=True, verbose_name=b'Terms and Conditions'),
        ),
        migrations.AddField(
            model_name='formpage',
            name='terms_and_conditions',
            field=models.ForeignKey(blank=True, to='wagtaildocs.Document', help_text=b'This document will be shown as the Terms and Conditions document.', null=True, verbose_name=b'Terms and Conditions'),
        ),
    ]
