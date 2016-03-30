# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import wagtail.wagtailcore.fields
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0020_add_index_on_page_first_published_at'),
        ('rca_ee', '0002_coursedocument'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookingFormField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('label', models.CharField(help_text='The label of the form field', max_length=255, verbose_name='Label')),
                ('field_type', models.CharField(max_length=16, verbose_name='Field type', choices=[('singleline', 'Single line text'), ('multiline', 'Multi-line text'), ('email', 'Email'), ('number', 'Number'), ('url', 'URL'), ('checkbox', 'Checkbox'), ('checkboxes', 'Checkboxes'), ('dropdown', 'Drop down'), ('radio', 'Radio buttons'), ('date', 'Date'), ('datetime', 'Date/time')])),
                ('required', models.BooleanField(default=True, verbose_name='Required')),
                ('choices', models.CharField(help_text='Comma separated list of choices. Only applicable in checkboxes, radio and dropdown.', max_length=512, verbose_name='Choices', blank=True)),
                ('default_value', models.CharField(help_text='Default value. Comma separated values supported for checkboxes.', max_length=255, verbose_name='Default value', blank=True)),
                ('help_text', models.CharField(max_length=255, verbose_name='Help text', blank=True)),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BookingFormPage',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('intro', wagtail.wagtailcore.fields.RichTextField(blank=True)),
                ('thank_you_text', wagtail.wagtailcore.fields.RichTextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='ExtendedAbstractEmailForm',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('to_address', models.CharField(help_text='Optional - form submissions will be emailed to this address', max_length=255, verbose_name='To address', blank=True)),
                ('from_address', models.CharField(max_length=255, verbose_name='From address', blank=True)),
                ('subject', models.CharField(max_length=255, verbose_name='Subject', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='ExtendedAbstractForm',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.RemoveField(
            model_name='formpage',
            name='from_address',
        ),
        migrations.RemoveField(
            model_name='formpage',
            name='page_ptr',
        ),
        migrations.RemoveField(
            model_name='formpage',
            name='subject',
        ),
        migrations.RemoveField(
            model_name='formpage',
            name='to_address',
        ),
        migrations.AddField(
            model_name='formfield',
            name='new_field_type',
            field=models.CharField(default='', max_length=16, verbose_name='Field type', choices=[('singleline', 'Single line text'), ('multiline', 'Multi-line text'), ('email', 'Email'), ('number', 'Number'), ('url', 'URL'), ('checkbox', 'Checkbox'), ('checkboxes', 'Checkboxes'), ('dropdown', 'Drop down'), ('radio', 'Radio buttons'), ('date', 'Date'), ('datetime', 'Date/time'), (b'hidden', 'Hidden field (not editable by user)')]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='bookingformfield',
            name='page',
            field=modelcluster.fields.ParentalKey(related_name='form_fields', to='rca_ee.BookingFormPage'),
        ),
        migrations.AddField(
            model_name='formpage',
            name='extendedabstractemailform_ptr',
            field=models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, default='', serialize=False, to='rca_ee.ExtendedAbstractEmailForm'),
            preserve_default=False,
        ),
    ]
