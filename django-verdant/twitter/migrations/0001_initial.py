# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import twitter.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Tweet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tweet_id', models.BigIntegerField(unique=True)),
                ('user_id', models.BigIntegerField()),
                ('user_screen_name', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField()),
                ('text', models.TextField()),
                ('payload', twitter.fields.JSONField(default=b'{}')),
            ],
        ),
    ]
