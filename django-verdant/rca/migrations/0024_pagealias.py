# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0020_add_index_on_page_first_published_at'),
        ('rca', '0023_auto_20160225_1055'),
    ]

    operations = [
        migrations.CreateModel(
            name='PageAlias',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('external_url', models.URLField(null=True, verbose_name=b'External link', blank=True)),
                ('listing_intro', models.TextField(blank=True)),
                ('alias', models.ForeignKey(related_name='aliases', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='wagtailcore.Page', null=True)),
                ('feed_image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
    ]
