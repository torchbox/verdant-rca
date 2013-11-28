# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    # ensure that this migration happens before the 'initial' migration in the new verdantcore app tries to create the tables.
    # (That migration will need to be faked after this one has been run.)
    needed_by = (
        ("verdantcore", "0001_initial"),
    )

    def forwards(self, orm):
        # move Page from core app to verdantcore app
        db.rename_table('core_page', 'verdantcore_page')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='core', model='page').update(app_label='verdantcore')

        # move PageRevision from core app to verdantcore app
        db.rename_table('core_pagerevision', 'verdantcore_pagerevision')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='core', model='pagerevision').update(app_label='verdantcore')

        # move Site from core app to verdantcore app
        db.rename_table('core_site', 'verdantcore_site')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='core', model='site').update(app_label='verdantcore')


    def backwards(self, orm):
        db.rename_table('verdantcore_page', 'core_page')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='verdantcore', model='page').update(app_label='core')

        db.rename_table('verdantcore_pagerevision', 'core_pagerevision')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='verdantcore', model='pagerevision').update(app_label='core')

        db.rename_table('verdantcore_site', 'core_site')
        if not db.dry_run:
            orm['contenttypes.contenttype'].objects.filter(app_label='verdantcore', model='site').update(app_label='core')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
    }

    complete_apps = ['core']