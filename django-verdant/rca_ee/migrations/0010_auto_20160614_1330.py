# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca_ee', '0009_auto_nullable_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookingformfield',
            name='choices',
            field=models.CharField(help_text='Comma separated list of choices. Only applicable in checkboxes, radio and dropdown.', max_length=512, verbose_name='choices', blank=True),
        ),
        migrations.AlterField(
            model_name='bookingformfield',
            name='default_value',
            field=models.CharField(help_text='Default value. Comma separated values supported for checkboxes.', max_length=255, verbose_name='default value', blank=True),
        ),
        migrations.AlterField(
            model_name='bookingformfield',
            name='field_type',
            field=models.CharField(max_length=16, verbose_name='field type', choices=[('singleline', 'Single line text'), ('multiline', 'Multi-line text'), ('email', 'Email'), ('number', 'Number'), ('url', 'URL'), ('checkbox', 'Checkbox'), ('checkboxes', 'Checkboxes'), ('dropdown', 'Drop down'), ('radio', 'Radio buttons'), ('date', 'Date'), ('datetime', 'Date/time')]),
        ),
        migrations.AlterField(
            model_name='bookingformfield',
            name='help_text',
            field=models.CharField(max_length=255, verbose_name='help text', blank=True),
        ),
        migrations.AlterField(
            model_name='bookingformfield',
            name='label',
            field=models.CharField(help_text='The label of the form field', max_length=255, verbose_name='label'),
        ),
        migrations.AlterField(
            model_name='bookingformfield',
            name='required',
            field=models.BooleanField(default=True, verbose_name='required'),
        ),
        migrations.AlterField(
            model_name='extendedabstractemailform',
            name='from_address',
            field=models.CharField(max_length=255, verbose_name='from address', blank=True),
        ),
        migrations.AlterField(
            model_name='extendedabstractemailform',
            name='subject',
            field=models.CharField(max_length=255, verbose_name='subject', blank=True),
        ),
        migrations.AlterField(
            model_name='extendedabstractemailform',
            name='to_address',
            field=models.CharField(help_text='Optional - form submissions will be emailed to this address', max_length=255, verbose_name='to address', blank=True),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='choices',
            field=models.CharField(help_text='Comma separated list of choices. Only applicable in checkboxes, radio and dropdown.', max_length=512, verbose_name='choices', blank=True),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='default_value',
            field=models.CharField(help_text='Default value. Comma separated values supported for checkboxes.', max_length=255, verbose_name='default value', blank=True),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='field_type',
            field=models.CharField(max_length=16, verbose_name='field type', choices=[('singleline', 'Single line text'), ('multiline', 'Multi-line text'), ('email', 'Email'), ('number', 'Number'), ('url', 'URL'), ('checkbox', 'Checkbox'), ('checkboxes', 'Checkboxes'), ('dropdown', 'Drop down'), ('radio', 'Radio buttons'), ('date', 'Date'), ('datetime', 'Date/time')]),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='help_text',
            field=models.CharField(max_length=255, verbose_name='help text', blank=True),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='label',
            field=models.CharField(help_text='The label of the form field', max_length=255, verbose_name='label'),
        ),
        migrations.AlterField(
            model_name='formfield',
            name='required',
            field=models.BooleanField(default=True, verbose_name='required'),
        ),
    ]
