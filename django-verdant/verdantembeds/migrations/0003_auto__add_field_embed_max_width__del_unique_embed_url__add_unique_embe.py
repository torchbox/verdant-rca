# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Embed', fields ['url']
        db.delete_unique(u'verdantembeds_embed', ['url'])

        # Adding field 'Embed.max_width'
        db.add_column(u'verdantembeds_embed', 'max_width',
                      self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True),
                      keep_default=False)

        # Adding unique constraint on 'Embed', fields ['url', 'max_width']
        db.create_unique(u'verdantembeds_embed', ['url', 'max_width'])


    def backwards(self, orm):
        # Removing unique constraint on 'Embed', fields ['url', 'max_width']
        db.delete_unique(u'verdantembeds_embed', ['url', 'max_width'])

        # Deleting field 'Embed.max_width'
        db.delete_column(u'verdantembeds_embed', 'max_width')

        # Adding unique constraint on 'Embed', fields ['url']
        db.create_unique(u'verdantembeds_embed', ['url'])


    models = {
        u'verdantembeds.embed': {
            'Meta': {'unique_together': "(('url', 'max_width'),)", 'object_name': 'Embed'},
            'height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'max_width': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'thumbnail_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['verdantembeds']