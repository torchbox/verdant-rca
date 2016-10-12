# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-10-12 16:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields
import wagtail.wagtailcore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0029_unicode_slugfield_dj19'),
        ('rca', '0045_newstudentpage_ad_username'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactUsPageGeneralEnquiries',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('text', wagtail.wagtailcore.fields.RichTextField(blank=True, help_text=b"You can specify custom text, if you don't want to use a Contact snippet.")),
                ('contact_snippet', models.ForeignKey(blank=True, help_text=b'', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='rca.ContactSnippet')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ContactUsPageMiddleColumnLinks',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('link_page', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='wagtailcore.Page')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='contactuspage',
            name='feed_image',
        ),
        migrations.AddField(
            model_name='contactuspage',
            name='body',
            field=wagtail.wagtailcore.fields.RichTextField(blank=True, help_text=b''),
        ),
        migrations.AddField(
            model_name='contactuspage',
            name='collapse_upcoming_events',
            field=models.BooleanField(default=False, help_text=b''),
        ),
        migrations.AddField(
            model_name='contactuspage',
            name='middle_column_map',
            field=models.TextField(blank=True, help_text=b''),
        ),
        migrations.AddField(
            model_name='contactuspage',
            name='twitter_feed',
            field=models.CharField(blank=True, help_text=b'Replace the default Twitter feed by providing an alternative Twitter handle (without the @ symbol)', max_length=255),
        ),
        migrations.AddField(
            model_name='contactuspagemiddlecolumnlinks',
            name='page',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='middle_column_links', to='rca.ContactUsPage'),
        ),
        migrations.AddField(
            model_name='contactuspagegeneralenquiries',
            name='page',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='general_enquiries', to='rca.ContactUsPage'),
        ),
    ]
