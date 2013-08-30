# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Site'
        db.create_table(u'core_site', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('hostname', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('root_page', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Page'])),
        ))
        db.send_create_signal(u'core', ['Site'])

        # Adding model 'Page'
        db.create_table(u'core_page', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='subpages', null=True, to=orm['core.Page'])),
        ))
        db.send_create_signal(u'core', ['Page'])


    def backwards(self, orm):
        # Deleting model 'Site'
        db.delete_table(u'core_site')

        # Deleting model 'Page'
        db.delete_table(u'core_page')


    models = {
        u'core.page': {
            'Meta': {'object_name': 'Page'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subpages'", 'null': 'True', 'to': u"orm['core.Page']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'core.site': {
            'Meta': {'object_name': 'Site'},
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'root_page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Page']"})
        }
    }

    complete_apps = ['core']