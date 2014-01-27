# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'SearchTerms'
        db.create_table(u'verdantsearch_searchterms', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('terms', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal(u'verdantsearch', ['SearchTerms'])

        # Adding model 'SearchTermsDailyHits'
        db.create_table(u'verdantsearch_searchtermsdailyhits', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('terms', self.gf('django.db.models.fields.related.ForeignKey')(related_name='daily_hits', to=orm['verdantsearch.SearchTerms'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('hits', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'verdantsearch', ['SearchTermsDailyHits'])

        # Adding unique constraint on 'SearchTermsDailyHits', fields ['terms', 'date']
        db.create_unique(u'verdantsearch_searchtermsdailyhits', ['terms_id', 'date'])

        # Adding model 'EditorsPick'
        db.create_table(u'verdantsearch_editorspick', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('terms', self.gf('django.db.models.fields.related.ForeignKey')(related_name='editors_picks', to=orm['verdantsearch.SearchTerms'])),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wagtailcore.Page'])),
            ('sort_order', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'verdantsearch', ['EditorsPick'])


    def backwards(self, orm):
        # Removing unique constraint on 'SearchTermsDailyHits', fields ['terms', 'date']
        db.delete_unique(u'verdantsearch_searchtermsdailyhits', ['terms_id', 'date'])

        # Deleting model 'SearchTerms'
        db.delete_table(u'verdantsearch_searchterms')

        # Deleting model 'SearchTermsDailyHits'
        db.delete_table(u'verdantsearch_searchtermsdailyhits')

        # Deleting model 'EditorsPick'
        db.delete_table(u'verdantsearch_editorspick')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'wagtailcore.page': {
            'Meta': {'object_name': 'Page'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pages'", 'to': u"orm['contenttypes.ContentType']"}),
            'depth': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'feed_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'has_unpublished_changes': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'live': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'numchild': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'seo_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'show_in_menus': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url_path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'rca.rcaimage': {
            'Meta': {'object_name': 'RcaImage'},
            'alt': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'dimensions': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'eprint_docid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'height': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'medium': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'permission': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'photographer': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'rca_content_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'width': ('django.db.models.fields.IntegerField', [], {}),
            'year': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'verdantsearch.editorspick': {
            'Meta': {'ordering': "('sort_order',)", 'object_name': 'EditorsPick'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['wagtailcore.Page']"}),
            'sort_order': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'terms': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'editors_picks'", 'to': u"orm['verdantsearch.SearchTerms']"})
        },
        u'verdantsearch.searchterms': {
            'Meta': {'object_name': 'SearchTerms'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'terms': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'verdantsearch.searchtermsdailyhits': {
            'Meta': {'unique_together': "(('terms', 'date'),)", 'object_name': 'SearchTermsDailyHits'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'hits': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'terms': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'daily_hits'", 'to': u"orm['verdantsearch.SearchTerms']"})
        },
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