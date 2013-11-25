# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'NewsItemRelatedLink'
        db.delete_table(u'rca_newsitemrelatedlink')

        # Adding model 'RelatedLink'
        db.create_table(u'rca_relatedlink', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(related_name='related_links', to=orm['core.Page'])),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('link_text', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['verdantimages.Image'])),
        ))
        db.send_create_signal(u'rca', ['RelatedLink'])


    def backwards(self, orm):
        # Adding model 'NewsItemRelatedLink'
        db.create_table(u'rca_newsitemrelatedlink', (
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', null=True, to=orm['verdantimages.Image'], blank=True)),
            ('link_text', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('news_item', self.gf('django.db.models.fields.related.ForeignKey')(related_name='related_links', to=orm['rca.NewsItem'])),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'rca', ['NewsItemRelatedLink'])

        # Deleting model 'RelatedLink'
        db.delete_table(u'rca_relatedlink')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'core.page': {
            'Meta': {'object_name': 'Page'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pages'", 'to': u"orm['contenttypes.ContentType']"}),
            'depth': ('django.db.models.fields.PositiveIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'numchild': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'rca.authorpage': {
            'Meta': {'object_name': 'AuthorPage', '_ormbases': [u'rca.EditorialPage']},
            u'editorialpage_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['rca.EditorialPage']", 'unique': 'True', 'primary_key': 'True'}),
            'mugshot': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['verdantimages.Image']"})
        },
        u'rca.authorsindex': {
            'Meta': {'object_name': 'AuthorsIndex', '_ormbases': [u'core.Page']},
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'rca.editorialpage': {
            'Meta': {'object_name': 'EditorialPage', '_ormbases': [u'core.Page']},
            'body': ('core.fields.RichTextField', [], {}),
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'rca.newsindex': {
            'Meta': {'object_name': 'NewsIndex', '_ormbases': [u'core.Page']},
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'rca.newsitem': {
            'Meta': {'object_name': 'NewsItem', '_ormbases': [u'rca.EditorialPage']},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'news_items'", 'null': 'True', 'to': u"orm['rca.AuthorPage']"}),
            u'editorialpage_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['rca.EditorialPage']", 'unique': 'True', 'primary_key': 'True'}),
            'lead_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['verdantimages.Image']"})
        },
        u'rca.relatedlink': {
            'Meta': {'object_name': 'RelatedLink'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['verdantimages.Image']"}),
            'link_text': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'related_links'", 'to': u"orm['core.Page']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'verdantimages.image': {
            'Meta': {'object_name': 'Image'},
            'file': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'height': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'width': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['rca']