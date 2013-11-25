# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'SavedEmbed.height'
        db.alter_column(u'django_embedly_savedembed', 'height', self.gf('django.db.models.fields.IntegerField')(null=True))

        # Changing field 'SavedEmbed.width'
        db.alter_column(u'django_embedly_savedembed', 'width', self.gf('django.db.models.fields.IntegerField')(null=True))

    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'SavedEmbed.height'
        raise RuntimeError("Cannot reverse this migration. 'SavedEmbed.height' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'SavedEmbed.width'
        raise RuntimeError("Cannot reverse this migration. 'SavedEmbed.width' and its values cannot be restored.")

    models = {
        u'django_embedly.savedembed': {
            'Meta': {'unique_together': "(('url', 'maxwidth'),)", 'object_name': 'SavedEmbed'},
            'height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'maxwidth': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['django_embedly']