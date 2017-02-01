# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2017-02-01 09:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0029_unicode_slugfield_dj19'),
        ('rca', '0074_schoolpage_school_brochure'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchoolPageFeaturedContent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('content', models.ForeignKey(blank=True, help_text=b'Featured content will be pinned on the page and be shown more prominently', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailcore.Page')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='schoolpage',
            name='featured_content_1',
        ),
        migrations.RemoveField(
            model_name='schoolpage',
            name='featured_content_2',
        ),
        migrations.RemoveField(
            model_name='schoolpage',
            name='featured_content_3',
        ),
        migrations.RemoveField(
            model_name='schoolpage',
            name='featured_content_4',
        ),
        migrations.RemoveField(
            model_name='schoolpage',
            name='featured_content_5',
        ),
        migrations.AddField(
            model_name='schoolpagefeaturedcontent',
            name='page',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='featured_content', to='rca.SchoolPage'),
        ),
    ]
