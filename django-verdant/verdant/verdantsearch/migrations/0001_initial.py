# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'SearchTest'
        db.create_table(u'verdantsearch_searchtest', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('content', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'verdantsearch', ['SearchTest'])

        # Adding model 'SearchTestChild'
        db.create_table(u'verdantsearch_searchtestchild', (
            (u'searchtest_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['verdantsearch.SearchTest'], unique=True, primary_key=True)),
            ('extra_content', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'verdantsearch', ['SearchTestChild'])


    def backwards(self, orm):
        # Deleting model 'SearchTest'
        db.delete_table(u'verdantsearch_searchtest')

        # Deleting model 'SearchTestChild'
        db.delete_table(u'verdantsearch_searchtestchild')


    models = {
        u'verdantsearch.searchtest': {
            'Meta': {'object_name': 'SearchTest'},
            'content': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'verdantsearch.searchtestchild': {
            'Meta': {'object_name': 'SearchTestChild', '_ormbases': [u'verdantsearch.SearchTest']},
            'extra_content': ('django.db.models.fields.TextField', [], {}),
            u'searchtest_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['verdantsearch.SearchTest']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['verdantsearch']