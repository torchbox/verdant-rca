# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import wagtail.wagtailimages.models
import django.db.models.deletion
from django.conf import settings
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0038_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rcaimage',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='created at', db_index=True),
        ),
        migrations.AlterField(
            model_name='rcaimage',
            name='file',
            field=models.ImageField(height_field='height', upload_to=wagtail.wagtailimages.models.get_upload_to, width_field='width', verbose_name='file'),
        ),
        migrations.AlterField(
            model_name='rcaimage',
            name='height',
            field=models.IntegerField(verbose_name='height', editable=False),
        ),
        migrations.AlterField(
            model_name='rcaimage',
            name='tags',
            field=taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text=None, verbose_name='tags'),
        ),
        migrations.AlterField(
            model_name='rcaimage',
            name='title',
            field=models.CharField(max_length=255, verbose_name='title'),
        ),
        migrations.AlterField(
            model_name='rcaimage',
            name='uploaded_by_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='uploaded by user'),
        ),
        migrations.AlterField(
            model_name='rcaimage',
            name='width',
            field=models.IntegerField(verbose_name='width', editable=False),
        ),
    ]
