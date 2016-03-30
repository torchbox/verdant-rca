# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rca_ee', '0003_auto_20160330_1730'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bookingformpage',
            name='page_ptr',
        ),
        migrations.AddField(
            model_name='bookingformfield',
            name='new_field_type',
            field=models.CharField(default='', max_length=16, verbose_name='Field type', choices=[('singleline', 'Single line text'), ('multiline', 'Multi-line text'), ('email', 'Email'), ('number', 'Number'), ('url', 'URL'), ('checkbox', 'Checkbox'), ('checkboxes', 'Checkboxes'), ('dropdown', 'Drop down'), ('radio', 'Radio buttons'), ('date', 'Date'), ('datetime', 'Date/time'), (b'multigroup', 'Grouped option field (extended syntax, see documentation)'), (b'hidden', 'Hidden field (not editable by user)')]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='bookingformpage',
            name='extendedabstractform_ptr',
            field=models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, default='', serialize=False, to='rca_ee.ExtendedAbstractForm'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='formfield',
            name='new_field_type',
            field=models.CharField(max_length=16, verbose_name='Field type', choices=[('singleline', 'Single line text'), ('multiline', 'Multi-line text'), ('email', 'Email'), ('number', 'Number'), ('url', 'URL'), ('checkbox', 'Checkbox'), ('checkboxes', 'Checkboxes'), ('dropdown', 'Drop down'), ('radio', 'Radio buttons'), ('date', 'Date'), ('datetime', 'Date/time'), (b'multigroup', 'Grouped option field (extended syntax, see documentation)'), (b'hidden', 'Hidden field (not editable by user)')]),
        ),
    ]
