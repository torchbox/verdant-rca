# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields
import wagtail.wagtailcore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0020_add_index_on_page_first_published_at'),
        ('rca', '0016_auto_20151106_0938'),
    ]

    operations = [
        migrations.CreateModel(
            name='LightboxGalleryPage',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('social_text', models.CharField(help_text=b'', max_length=255, blank=True)),
                ('intro', wagtail.wagtailcore.fields.RichTextField(help_text=b'', blank=True)),
                ('listing_intro', models.CharField(help_text=b'Used only on pages listing Lightbox Galleries', max_length=100, blank=True)),
                ('feed_image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio.', null=True)),
                ('social_image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page', models.Model),
        ),
        migrations.CreateModel(
            name='LightboxGalleryPageItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('embedly_url', models.URLField(help_text=b'A video to show instead of an image', verbose_name=b'Video URL', blank=True)),
                ('image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'', null=True)),
                ('page', modelcluster.fields.ParentalKey(related_name='gallery_items', to='rca.LightboxGalleryPage')),
                ('poster_image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'A still image of the video to display when not playing.', null=True, verbose_name=b'Video still image')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
    ]
