# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    depends_on = (
        ("wagtailcore", "0002_initial_data"),
    )

    def forwards(self, orm):
        # Adding model 'Image'
        db.create_table(u'verdantimages_image', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('file', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('width', self.gf('django.db.models.fields.IntegerField')()),
            ('height', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'verdantimages', ['Image'])

        # Adding model 'Format'
        db.create_table(u'verdantimages_format', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('spec', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
        ))
        db.send_create_signal(u'verdantimages', ['Format'])

        # Adding model 'Rendition'
        db.create_table(u'verdantimages_rendition', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(related_name='renditions', to=orm['verdantimages.Image'])),
            ('format', self.gf('django.db.models.fields.related.ForeignKey')(related_name='renditions', to=orm['verdantimages.Format'])),
            ('file', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('width', self.gf('django.db.models.fields.IntegerField')()),
            ('height', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'verdantimages', ['Rendition'])


    def backwards(self, orm):
        # Deleting model 'Image'
        db.delete_table(u'verdantimages_image')

        # Deleting model 'Format'
        db.delete_table(u'verdantimages_format')

        # Deleting model 'Rendition'
        db.delete_table(u'verdantimages_rendition')


    models = {
        u'verdantimages.format': {
            'Meta': {'object_name': 'Format'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'spec': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        u'verdantimages.image': {
            'Meta': {'object_name': 'Image'},
            'file': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'height': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'width': ('django.db.models.fields.IntegerField', [], {})
        },
        u'verdantimages.rendition': {
            'Meta': {'object_name': 'Rendition'},
            'file': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'format': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'renditions'", 'to': u"orm['verdantimages.Format']"}),
            'height': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'renditions'", 'to': u"orm['verdantimages.Image']"}),
            'width': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['verdantimages']