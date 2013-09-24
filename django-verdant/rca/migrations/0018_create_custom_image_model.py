# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'RcaImage'
        db.create_table(u'rca_rcaimage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('file', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('width', self.gf('django.db.models.fields.IntegerField')()),
            ('height', self.gf('django.db.models.fields.IntegerField')()),
            ('alt', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('creator', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('year', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('medium', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('dimensions', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('permission', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('photographer', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal(u'rca', ['RcaImage'])

        # copy image data from verdantimages.Image into rca.RcaImage
        for image in orm['verdantimages.Image'].objects.order_by('id'):
            orm['rca.RcaImage'].objects.create(
                id=image.id, title=image.title, file=image.file, width=image.width, height=image.height
            )
        db.execute("select setval('rca_rcaimage_id_seq', (SELECT MAX(id) FROM rca_rcaimage))")

        # Adding model 'RcaRendition'
        db.create_table(u'rca_rcarendition', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('filter', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['verdantimages.Filter'])),
            ('file', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('width', self.gf('django.db.models.fields.IntegerField')()),
            ('height', self.gf('django.db.models.fields.IntegerField')()),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(related_name='renditions', to=orm['rca.RcaImage'])),
        ))
        db.send_create_signal(u'rca', ['RcaRendition'])


        # Changing field 'StandardPageCarouselItem.image'
        db.alter_column(u'rca_standardpagecarouselitem', 'image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'StandardPageCarouselItem.poster_image'
        db.alter_column(u'rca_standardpagecarouselitem', 'poster_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'EventItemCarouselItem.image'
        db.alter_column(u'rca_eventitemcarouselitem', 'image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'StudentPage.social_image'
        db.alter_column(u'rca_studentpage', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'RelatedLink.image'
        db.alter_column(u'rca_relatedlink', 'image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'JobPage.social_image'
        db.alter_column(u'rca_jobpage', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'EventItem.social_image'
        db.alter_column(u'rca_eventitem', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'ResearchInnovationPage.social_image'
        db.alter_column(u'rca_researchinnovationpage', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'NewsItem.social_image'
        db.alter_column(u'rca_newsitem', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'AuthorPage.mugshot'
        db.alter_column(u'rca_authorpage', 'mugshot_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'HomePage.social_image'
        db.alter_column(u'rca_homepage', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'ResearchItem.social_image'
        db.alter_column(u'rca_researchitem', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'ContactUsPage.social_image'
        db.alter_column(u'rca_contactuspage', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'StandardPage.social_image'
        db.alter_column(u'rca_standardpage', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'StandardIndex.social_image'
        db.alter_column(u'rca_standardindex', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'JobsIndex.social_image'
        db.alter_column(u'rca_jobsindex', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'ProgrammePageOurSites.image'
        db.alter_column(u'rca_programmepageoursites', 'image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'GalleryPage.social_image'
        db.alter_column(u'rca_gallerypage', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'NewsItemCarouselItem.image'
        db.alter_column(u'rca_newsitemcarouselitem', 'image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'NewsItemCarouselItem.poster_image'
        db.alter_column(u'rca_newsitemcarouselitem', 'poster_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'RcaNowPage.social_image'
        db.alter_column(u'rca_rcanowpage', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'CurrentResearchPage.social_image'
        db.alter_column(u'rca_currentresearchpage', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'ProgrammePageCarouselItem.image'
        db.alter_column(u'rca_programmepagecarouselitem', 'image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'StaffPage.social_image'
        db.alter_column(u'rca_staffpage', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'RcaNowIndex.social_image'
        db.alter_column(u'rca_rcanowindex', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'EventItemSpeaker.image'
        db.alter_column(u'rca_eventitemspeaker', 'image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'ProgrammePageStudentStory.image'
        db.alter_column(u'rca_programmepagestudentstory', 'image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

        # Changing field 'ProgrammePageFacilities.image'
        db.alter_column(u'rca_programmepagefacilities', 'image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['rca.RcaImage']))

    def backwards(self, orm):
        # Deleting model 'RcaImage'
        db.delete_table(u'rca_rcaimage')

        # Deleting model 'RcaRendition'
        db.delete_table(u'rca_rcarendition')


        # Changing field 'StandardPageCarouselItem.image'
        db.alter_column(u'rca_standardpagecarouselitem', 'image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'StandardPageCarouselItem.poster_image'
        db.alter_column(u'rca_standardpagecarouselitem', 'poster_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'EventItemCarouselItem.image'
        db.alter_column(u'rca_eventitemcarouselitem', 'image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'StudentPage.social_image'
        db.alter_column(u'rca_studentpage', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'RelatedLink.image'
        db.alter_column(u'rca_relatedlink', 'image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'JobPage.social_image'
        db.alter_column(u'rca_jobpage', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'EventItem.social_image'
        db.alter_column(u'rca_eventitem', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'ResearchInnovationPage.social_image'
        db.alter_column(u'rca_researchinnovationpage', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'NewsItem.social_image'
        db.alter_column(u'rca_newsitem', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'AuthorPage.mugshot'
        db.alter_column(u'rca_authorpage', 'mugshot_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'HomePage.social_image'
        db.alter_column(u'rca_homepage', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'ResearchItem.social_image'
        db.alter_column(u'rca_researchitem', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'ContactUsPage.social_image'
        db.alter_column(u'rca_contactuspage', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'StandardPage.social_image'
        db.alter_column(u'rca_standardpage', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'StandardIndex.social_image'
        db.alter_column(u'rca_standardindex', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'JobsIndex.social_image'
        db.alter_column(u'rca_jobsindex', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'ProgrammePageOurSites.image'
        db.alter_column(u'rca_programmepageoursites', 'image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'GalleryPage.social_image'
        db.alter_column(u'rca_gallerypage', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'NewsItemCarouselItem.image'
        db.alter_column(u'rca_newsitemcarouselitem', 'image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'NewsItemCarouselItem.poster_image'
        db.alter_column(u'rca_newsitemcarouselitem', 'poster_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'RcaNowPage.social_image'
        db.alter_column(u'rca_rcanowpage', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'CurrentResearchPage.social_image'
        db.alter_column(u'rca_currentresearchpage', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'ProgrammePageCarouselItem.image'
        db.alter_column(u'rca_programmepagecarouselitem', 'image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'StaffPage.social_image'
        db.alter_column(u'rca_staffpage', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'RcaNowIndex.social_image'
        db.alter_column(u'rca_rcanowindex', 'social_image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'EventItemSpeaker.image'
        db.alter_column(u'rca_eventitemspeaker', 'image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'ProgrammePageStudentStory.image'
        db.alter_column(u'rca_programmepagestudentstory', 'image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

        # Changing field 'ProgrammePageFacilities.image'
        db.alter_column(u'rca_programmepagefacilities', 'image_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['verdantimages.Image']))

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
            'mugshot': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"})
        },
        u'rca.authorsindex': {
            'Meta': {'object_name': 'AuthorsIndex', '_ormbases': [u'core.Page']},
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'rca.contactuspage': {
            'Meta': {'object_name': 'ContactUsPage', '_ormbases': [u'core.Page']},
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'social_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'social_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'rca.currentresearchpage': {
            'Meta': {'object_name': 'CurrentResearchPage', '_ormbases': [u'core.Page']},
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'social_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'social_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'rca.editorialpage': {
            'Meta': {'object_name': 'EditorialPage', '_ormbases': [u'core.Page']},
            'body': ('core.fields.RichTextField', [], {}),
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'rca.eventitem': {
            'Meta': {'object_name': 'EventItem', '_ormbases': [u'core.Page']},
            'audience': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'cost': ('core.fields.RichTextField', [], {'blank': 'True'}),
            'date_from': ('django.db.models.fields.DateField', [], {}),
            'date_to': ('django.db.models.fields.DateField', [], {}),
            'gallery': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'listing_intro': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'related_programme': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'event_item'", 'null': 'True', 'to': u"orm['rca.ProgrammePage']"}),
            'related_school': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'event_item'", 'null': 'True', 'to': u"orm['rca.SchoolPage']"}),
            'show_on_homepage': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'signup_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'social_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'social_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'specific_directions': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'specific_directions_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'times': ('core.fields.RichTextField', [], {'blank': 'True'})
        },
        u'rca.eventitemcarouselitem': {
            'Meta': {'object_name': 'EventItemCarouselItem'},
            'embedly_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'carousel_items'", 'to': u"orm['rca.EventItem']"})
        },
        u'rca.eventitemspeaker': {
            'Meta': {'object_name': 'EventItemSpeaker'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'speakers'", 'to': u"orm['rca.EventItem']"}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'rca.gallerypage': {
            'Meta': {'object_name': 'GalleryPage', '_ormbases': [u'core.Page']},
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'social_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'social_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'rca.homepage': {
            'Meta': {'object_name': 'HomePage', '_ormbases': [u'core.Page']},
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'social_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'social_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'rca.jobpage': {
            'Meta': {'object_name': 'JobPage', '_ormbases': [u'core.Page']},
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'social_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'social_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'rca.jobsindex': {
            'Meta': {'object_name': 'JobsIndex', '_ormbases': [u'core.Page']},
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'social_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'social_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'rca.newsindex': {
            'Meta': {'object_name': 'NewsIndex', '_ormbases': [u'core.Page']},
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'rca.newsitem': {
            'Meta': {'object_name': 'NewsItem', '_ormbases': [u'core.Page']},
            'area': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'news_items'", 'null': 'True', 'to': u"orm['rca.AuthorPage']"}),
            'body': ('core.fields.RichTextField', [], {}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'intro': ('core.fields.RichTextField', [], {}),
            'listing_intro': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'related_programme': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'news_item'", 'null': 'True', 'to': u"orm['rca.ProgrammePage']"}),
            'related_school': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'news_item'", 'null': 'True', 'to': u"orm['rca.SchoolPage']"}),
            'show_on_homepage': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'social_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'social_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'rca.newsitemcarouselitem': {
            'Meta': {'object_name': 'NewsItemCarouselItem'},
            'embedly_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'image_creator': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'image_dimensions': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'image_medium': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'image_photographer': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'image_year': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'overlay_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'carousel_items'", 'to': u"orm['rca.NewsItem']"}),
            'poster_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"})
        },
        u'rca.newsitemrelatedlink': {
            'Meta': {'object_name': 'NewsItemRelatedLink'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link_text': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'related_links'", 'to': u"orm['rca.NewsItem']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'rca.programmepage': {
            'Meta': {'object_name': 'ProgrammePage', '_ormbases': [u'core.Page']},
            'download_document_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'download_document_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'head_of_programme': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'head_of_programme_statement': ('core.fields.RichTextField', [], {}),
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'programme_video': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'rca.programmepagecarouselitem': {
            'Meta': {'object_name': 'ProgrammePageCarouselItem'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'carousel_items'", 'to': u"orm['rca.ProgrammePage']"}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'rca.programmepagefacilities': {
            'Meta': {'object_name': 'ProgrammePageFacilities'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'facilities'", 'to': u"orm['rca.ProgrammePage']"}),
            'text': ('core.fields.RichTextField', [], {})
        },
        u'rca.programmepageoursites': {
            'Meta': {'object_name': 'ProgrammePageOurSites'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'our_sites'", 'to': u"orm['rca.ProgrammePage']"}),
            'site_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'rca.programmepagerelatedlink': {
            'Meta': {'object_name': 'ProgrammePageRelatedLink'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link_text': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'related_links'", 'to': u"orm['rca.ProgrammePage']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'rca.programmepagestudentstory': {
            'Meta': {'object_name': 'ProgrammePageStudentStory'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'student_stories'", 'to': u"orm['rca.ProgrammePage']"}),
            'text': ('core.fields.RichTextField', [], {})
        },
        u'rca.rcaimage': {
            'Meta': {'object_name': 'RcaImage'},
            'alt': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'creator': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'dimensions': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'height': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'medium': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'permission': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'photographer': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'width': ('django.db.models.fields.IntegerField', [], {}),
            'year': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'rca.rcanowindex': {
            'Meta': {'object_name': 'RcaNowIndex', '_ormbases': [u'core.Page']},
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'social_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'social_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'rca.rcanowpage': {
            'Meta': {'object_name': 'RcaNowPage', '_ormbases': [u'core.Page']},
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'social_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'social_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'rca.rcarendition': {
            'Meta': {'object_name': 'RcaRendition'},
            'file': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['verdantimages.Filter']"}),
            'height': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'renditions'", 'to': u"orm['rca.RcaImage']"}),
            'width': ('django.db.models.fields.IntegerField', [], {})
        },
        u'rca.relateddocument': {
            'Meta': {'object_name': 'RelatedDocument'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['verdantdocs.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'related_documents'", 'to': u"orm['core.Page']"})
        },
        u'rca.relatedlink': {
            'Meta': {'object_name': 'RelatedLink'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'link_text': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'generic_related_links'", 'to': u"orm['core.Page']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'rca.researchinnovationpage': {
            'Meta': {'object_name': 'ResearchInnovationPage', '_ormbases': [u'core.Page']},
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'social_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'social_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'rca.researchitem': {
            'Meta': {'object_name': 'ResearchItem', '_ormbases': [u'core.Page']},
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'social_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'social_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'rca.schoolpage': {
            'Meta': {'object_name': 'SchoolPage', '_ormbases': [u'core.Page']},
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'rca.staffpage': {
            'Meta': {'object_name': 'StaffPage', '_ormbases': [u'core.Page']},
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'social_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'social_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'rca.standardindex': {
            'Meta': {'object_name': 'StandardIndex', '_ormbases': [u'core.Page']},
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'social_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'social_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'rca.standardpage': {
            'Meta': {'object_name': 'StandardPage', '_ormbases': [u'core.Page']},
            'body': ('core.fields.RichTextField', [], {'blank': 'True'}),
            'intro': ('core.fields.RichTextField', [], {'blank': 'True'}),
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'social_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'social_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'rca.standardpagecarouselitem': {
            'Meta': {'object_name': 'StandardPageCarouselItem'},
            'embedly_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'image_creator': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'image_dimensions': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'image_medium': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'image_photographer': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'image_year': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'overlay_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'carousel_items'", 'to': u"orm['rca.StandardPage']"}),
            'poster_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"})
        },
        u'rca.standardpagerelatedlink': {
            'Meta': {'object_name': 'StandardPageRelatedLink'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link_text': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'related_links'", 'to': u"orm['rca.StandardPage']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        u'rca.studentpage': {
            'Meta': {'object_name': 'StudentPage', '_ormbases': [u'core.Page']},
            u'page_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['core.Page']", 'unique': 'True', 'primary_key': 'True'}),
            'social_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': u"orm['rca.RcaImage']"}),
            'social_text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_tagged_items'", 'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_items'", 'to': u"orm['taggit.Tag']"})
        },
        u'verdantdocs.document': {
            'Meta': {'object_name': 'Document'},
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'verdantimages.filter': {
            'Meta': {'object_name': 'Filter'},
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
        }
    }

    complete_apps = ['rca']