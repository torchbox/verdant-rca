# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0002_remove_duplicate_change_permissions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alumnipage',
            name='show_on_homepage',
            field=models.BooleanField(default=False, help_text=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='donationpage',
            name='show_on_homepage',
            field=models.BooleanField(default=False, help_text=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='eventitem',
            name='show_on_homepage',
            field=models.BooleanField(default=False, help_text=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='innovationrcaproject',
            name='show_on_homepage',
            field=models.BooleanField(default=False, help_text=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='jobpage',
            name='show_on_homepage',
            field=models.BooleanField(default=False, help_text=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='newsitem',
            name='show_on_homepage',
            field=models.BooleanField(default=False, help_text=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='oeformpage',
            name='show_on_homepage',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='pressrelease',
            name='show_on_homepage',
            field=models.BooleanField(default=False, help_text=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rcablogpage',
            name='show_on_homepage',
            field=models.BooleanField(default=False, help_text=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rcanowpage',
            name='show_on_homepage',
            field=models.BooleanField(default=False, help_text=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reachoutrcaproject',
            name='show_on_homepage',
            field=models.BooleanField(default=False, help_text=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='researchitem',
            name='show_on_homepage',
            field=models.BooleanField(default=False, help_text=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='reviewpage',
            name='show_on_homepage',
            field=models.BooleanField(default=False, help_text=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='staffpage',
            name='show_on_homepage',
            field=models.BooleanField(default=False, help_text=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='staffpage',
            name='show_on_programme_page',
            field=models.BooleanField(default=False, help_text=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='standardpage',
            name='show_on_homepage',
            field=models.BooleanField(default=False, help_text=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='studentpage',
            name='show_on_homepage',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sustainrcaproject',
            name='show_on_homepage',
            field=models.BooleanField(default=False, help_text=b''),
            preserve_default=True,
        ),
    ]
