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
        # Adding model 'EditorialPage'
        db.create_table(u'rca_editorialpage', (
            (u'page_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['wagtailcore.Page'], unique=True, primary_key=True)),
            ('body', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'rca', ['EditorialPage'])


    def backwards(self, orm):
        # Deleting model 'EditorialPage'
        db.delete_table(u'rca_editorialpage')


    models = {
        u'wagtailcore.page': {
            'Meta': {'object_name': 'Page'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subpages'", 'null': 'True', 'to': u"orm['wagtailcore.Page']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'rca.editorialpage': {
            'Meta': {'object_name': 'EditorialPage', '_ormbases': [u'wagtailcore.page']},
            'body': ('django.db.models.fields.TextField', [], {}),
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['wagtailcore.Page']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['rca']