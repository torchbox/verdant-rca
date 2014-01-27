# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'SearchTermsDailyHits', fields ['terms', 'date']
        db.delete_unique(u'verdantsearch_searchtermsdailyhits', ['terms_id', 'date'])

        # Deleting model 'EditorsPick'
        db.delete_table(u'verdantsearch_editorspick')

        # Deleting model 'SearchTerms'
        db.delete_table(u'verdantsearch_searchterms')

        # Deleting model 'SearchTermsDailyHits'
        db.delete_table(u'verdantsearch_searchtermsdailyhits')


    def backwards(self, orm):
        # Adding model 'EditorsPick'
        db.create_table(u'verdantsearch_editorspick', (
            ('terms', self.gf('django.db.models.fields.related.ForeignKey')(related_name='editors_picks', to=orm['verdantsearch.SearchTerms'])),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sort_order', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wagtailcore.Page'])),
        ))
        db.send_create_signal(u'verdantsearch', ['EditorsPick'])

        # Adding model 'SearchTerms'
        db.create_table(u'verdantsearch_searchterms', (
            ('terms', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'verdantsearch', ['SearchTerms'])

        # Adding model 'SearchTermsDailyHits'
        db.create_table(u'verdantsearch_searchtermsdailyhits', (
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('hits', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('terms', self.gf('django.db.models.fields.related.ForeignKey')(related_name='daily_hits', to=orm['verdantsearch.SearchTerms'])),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'verdantsearch', ['SearchTermsDailyHits'])

        # Adding unique constraint on 'SearchTermsDailyHits', fields ['terms', 'date']
        db.create_unique(u'verdantsearch_searchtermsdailyhits', ['terms_id', 'date'])


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