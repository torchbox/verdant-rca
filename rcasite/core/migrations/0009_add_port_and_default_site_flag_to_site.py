# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Site.port'
        db.add_column(u'core_site', 'port',
                      self.gf('django.db.models.fields.IntegerField')(default=80),
                      keep_default=False)

        # Adding field 'Site.is_default_site'
        db.add_column(u'core_site', 'is_default_site',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # set is_default_site to true for any sites with hostname "*",
        # and substitute in 'localhost' as the hostname
        orm['core.Site'].objects.filter(hostname='*').update(is_default_site=True, hostname='localhost')

    def backwards(self, orm):
        # set hostname back to "*" for any default sites
        orm['core.Site'].objects.filter(is_default_site=True).update(hostname='*')

        # Deleting field 'Site.port'
        db.delete_column(u'core_site', 'port')

        # Deleting field 'Site.is_default_site'
        db.delete_column(u'core_site', 'is_default_site')


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
        u'core.site': {
            'Meta': {'object_name': 'Site'},
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_default_site': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'port': ('django.db.models.fields.IntegerField', [], {'default': '80'}),
            'root_page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sites_rooted_here'", 'to': u"orm['core.Page']"})
        }
    }

    complete_apps = ['core']