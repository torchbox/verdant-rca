# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Tweet'
        db.create_table(u'twitter_tweet', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tweet_id', self.gf('django.db.models.fields.BigIntegerField')(unique=True)),
            ('user_id', self.gf('django.db.models.fields.BigIntegerField')()),
            ('user_screen_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('payload', self.gf('django.db.models.fields.TextField')(default='{}')),
        ))
        db.send_create_signal(u'twitter', ['Tweet'])


    def backwards(self, orm):
        # Deleting model 'Tweet'
        db.delete_table(u'twitter_tweet')


    models = {
        u'twitter.tweet': {
            'Meta': {'object_name': 'Tweet'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'payload': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'tweet_id': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True'}),
            'user_id': ('django.db.models.fields.BigIntegerField', [], {}),
            'user_screen_name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['twitter']