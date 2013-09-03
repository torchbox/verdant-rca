# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

from treebeard.numconv import NumConv


# stuff we need for converting numbers into strings for the path field
alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
NUMCONV = NumConv(len(alphabet), alphabet)
STEPLEN = 4


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Page.path'. NB Need to add unique constraint after we've populated it
        db.add_column(u'core_page', 'path',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255),
                      keep_default=False)

        # Adding field 'Page.depth'
        db.add_column(u'core_page', 'depth',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'Page.numchild'
        db.add_column(u'core_page', 'numchild',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # apply tree structure on nodes with parent None -
        # it will be applied to children recursively
        self.apply_tree(orm, None, '', 1)


    def apply_tree(self, orm, parent, prefix, depth):
        children = orm['core.Page'].objects.filter(parent=parent).order_by('title')
        for (i, page) in enumerate(children):
            page.depth = depth
            key = NUMCONV.int2str(i + 1)
            page.path = '%s%s%s' % (prefix, '0' * (STEPLEN - len(key)), key)

            child_count = self.apply_tree(orm, page, page.path, depth + 1)
            page.numchild = child_count
            page.save()
        return len(children)


    def backwards(self, orm):
        # Deleting field 'Page.path'
        db.delete_column(u'core_page', 'path')

        # Deleting field 'Page.depth'
        db.delete_column(u'core_page', 'depth')

        # Deleting field 'Page.numchild'
        db.delete_column(u'core_page', 'numchild')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'core.page': {
            'Meta': {'unique_together': "(('parent', 'slug'),)", 'object_name': 'Page'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pages'", 'to': u"orm['contenttypes.ContentType']"}),
            'depth': ('django.db.models.fields.PositiveIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'numchild': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subpages'", 'null': 'True', 'to': u"orm['core.Page']"}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'core.site': {
            'Meta': {'object_name': 'Site'},
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'root_page': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Page']"})
        }
    }

    complete_apps = ['core']