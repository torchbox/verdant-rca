# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import modelcluster.fields
import wagtail.wagtailcore.fields
import modelcluster.contrib.taggit


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        ('wagtailcore', '0019_verbose_names_cleanup'),
        ('wagtaildocs', '0003_add_verbose_names'),
        ('rca', '0015_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='PathwayPage',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('social_text', models.CharField(help_text=b'', max_length=255, blank=True)),
                ('collapse_upcoming_events', models.BooleanField(default=False, help_text=b'')),
                ('intro', wagtail.wagtailcore.fields.RichTextField(help_text=b'', blank=True)),
                ('body', wagtail.wagtailcore.fields.RichTextField(help_text=b'')),
                ('strapline', models.CharField(help_text=b'', max_length=255, blank=True)),
                ('middle_column_body', wagtail.wagtailcore.fields.RichTextField(help_text=b'', blank=True)),
                ('show_on_homepage', models.BooleanField(default=False, help_text=b'')),
                ('twitter_feed', models.CharField(help_text=b'Replace the default Twitter feed by providing an alternative Twitter handle (without the @ symbol)', max_length=255, blank=True)),
                ('related_school', models.CharField(blank=True, help_text=b'', max_length=255, choices=[(b'schoolofarchitecture', b'School of Architecture'), (b'schoolofcommunication', b'School of Communication'), (b'schoolofdesign', b'School of Design'), (b'schooloffineart', b'School of Fine Art'), (b'schoolofhumanities', b'School of Humanities'), (b'schoolofmaterial', b'School of Material'), (b'helenhamlyn', b'The Helen Hamlyn Centre for Design'), (b'rectorate', b'Rectorate'), (b'innovationrca', b'InnovationRCA')])),
                ('related_programme', models.CharField(blank=True, help_text=b'', max_length=255, choices=[(b'2015/16', ((b'animation', b'Animation'), (b'architecture', b'Architecture'), (b'ceramicsglass', b'Ceramics & Glass'), (b'contemporaryartpractice', b'Contemporary Art Practice'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'criticalwritinginartdesign', b'Critical Writing in Art & Design'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'designinteractions', b'Design Interactions'), (b'designproducts', b'Design Products'), (b'fashionmenswear', b'Fashion Menswear'), (b'fashionwomenswear', b'Fashion Womenswear'), (b'globalinnovationdesign', b'Global Innovation Design'), (b'historyofdesign', b'History of Design'), (b'informationexperiencedesign', b'Information Experience Design'), (b'innovationdesignengineering', b'Innovation Design Engineering'), (b'interiordesign', b'Interior Design'), (b'jewelleryandmetal', b'Jewellery & Metal'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'print', b'Print'), (b'sculpture', b'Sculpture'), (b'servicedesign', b'Service Design'), (b'textiles', b'Textiles'), (b'vehicledesign', b'Vehicle Design'), (b'visualcommunication', b'Visual Communication'))), (b'2014/15', ((b'animation', b'Animation'), (b'architecture', b'Architecture'), (b'ceramicsglass', b'Ceramics & Glass'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'criticalwritinginartdesign', b'Critical Writing in Art & Design'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'designinteractions', b'Design Interactions'), (b'designproducts', b'Design Products'), (b'fashionmenswear', b'Fashion Menswear'), (b'fashionwomenswear', b'Fashion Womenswear'), (b'globalinnovationdesign', b'Global Innovation Design'), (b'historyofdesign', b'History of Design'), (b'informationexperiencedesign', b'Information Experience Design'), (b'innovationdesignengineering', b'Innovation Design Engineering'), (b'interiordesign', b'Interior Design'), (b'jewelleryandmetal', b'Jewellery & Metal'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'), (b'servicedesign', b'Service Design'), (b'textiles', b'Textiles'), (b'vehicledesign', b'Vehicle Design'), (b'visualcommunication', b'Visual Communication'))), (b'2013/14', ((b'animation', b'Animation'), (b'architecture', b'Architecture'), (b'ceramicsglass', b'Ceramics & Glass'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'criticalwritinginartdesign', b'Critical Writing in Art & Design'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'designinteractions', b'Design Interactions'), (b'designproducts', b'Design Products'), (b'fashionmenswear', b'Fashion Menswear'), (b'fashionwomenswear', b'Fashion Womenswear'), (b'globalinnovationdesign', b'Global Innovation Design'), (b'goldsmithingsilversmithingmetalworkjewellery', b'Goldsmithing, Silversmithing, Metalwork & Jewellery'), (b'historyofdesign', b'History of Design'), (b'informationexperiencedesign', b'Information Experience Design'), (b'innovationdesignengineering', b'Innovation Design Engineering'), (b'interiordesign', b'Interior Design'), (b'jewelleryandmetal', b'Jewellery & Metal'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'), (b'servicedesign', b'Service Design'), (b'textiles', b'Textiles'), (b'vehicledesign', b'Vehicle Design'), (b'visualcommunication', b'Visual Communication'))), (b'2012/13', ((b'animation', b'Animation'), (b'architecture', b'Architecture'), (b'ceramicsglass', b'Ceramics & Glass'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'criticalwritinginartdesign', b'Critical Writing in Art & Design'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'designinteractions', b'Design Interactions'), (b'designproducts', b'Design Products'), (b'fashionmenswear', b'Fashion Menswear'), (b'fashionwomenswear', b'Fashion Womenswear'), (b'goldsmithingsilversmithingmetalworkjewellery', b'Goldsmithing, Silversmithing, Metalwork & Jewellery'), (b'historyofdesign', b'History of Design'), (b'innovationdesignengineering', b'Innovation Design Engineering'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'), (b'servicedesign', b'Service Design'), (b'textiles', b'Textiles'), (b'vehicledesign', b'Vehicle Design'), (b'visualcommunication', b'Visual Communication'))), (b'2011/12', ((b'animation', b'Animation'), (b'architecture', b'Architecture'), (b'ceramicsglass', b'Ceramics & Glass'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'criticalwritinginartdesign', b'Critical Writing in Art & Design'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'designinteractions', b'Design Interactions'), (b'designproducts', b'Design Products'), (b'fashionmenswear', b'Fashion Menswear'), (b'fashionwomenswear', b'Fashion Womenswear'), (b'goldsmithingsilversmithingmetalworkjewellery', b'Goldsmithing, Silversmithing, Metalwork & Jewellery'), (b'historyofdesign', b'History of Design'), (b'innovationdesignengineering', b'Innovation Design Engineering'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'), (b'textiles', b'Textiles'), (b'vehicledesign', b'Vehicle Design'), (b'visualcommunication', b'Visual Communication'))), (b'2010/11', ((b'animation', b'Animation'), (b'architecture', b'Architecture'), (b'ceramicsglass', b'Ceramics & Glass'), (b'communicationartdesign', b'Communication Art & Design'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'criticalwritinginartdesign', b'Critical Writing in Art & Design'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'designinteractions', b'Design Interactions'), (b'designproducts', b'Design Products'), (b'fashionmenswear', b'Fashion Menswear'), (b'fashionwomenswear', b'Fashion Womenswear'), (b'goldsmithingsilversmithingmetalworkjewellery', b'Goldsmithing, Silversmithing, Metalwork & Jewellery'), (b'historyofdesign', b'History of Design'), (b'innovationdesignengineering', b'Innovation Design Engineering'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'), (b'textiles', b'Textiles'), (b'vehicledesign', b'Vehicle Design'))), (b'2009/10', ((b'animation', b'Animation'), (b'architecture', b'Architecture'), (b'ceramicsglass', b'Ceramics & Glass'), (b'communicationartdesign', b'Communication Art & Design'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'criticalwritinginartdesign', b'Critical Writing in Art & Design'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'designinteractions', b'Design Interactions'), (b'designproducts', b'Design Products'), (b'fashionmenswear', b'Fashion Menswear'), (b'fashionwomenswear', b'Fashion Womenswear'), (b'goldsmithingsilversmithingmetalworkjewellery', b'Goldsmithing, Silversmithing, Metalwork & Jewellery'), (b'historyofdesign', b'History of Design'), (b'innovationdesignengineering', b'Innovation Design Engineering'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'), (b'textiles', b'Textiles'), (b'vehicledesign', b'Vehicle Design'))), (b'2008/09', ((b'animation', b'Animation'), (b'communicationartdesign', b'Communication Art & Design'), (b'conservation', b'Conservation'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'historyofdesign', b'History of Design'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'))), (b'2007/08', ((b'animation', b'Animation'), (b'communicationartdesign', b'Communication Art & Design'), (b'conservation', b'Conservation'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'historyofdesign', b'History of Design'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'))), (b'2006/07', ((b'animation', b'Animation'), (b'communicationartdesign', b'Communication Art & Design'), (b'conservation', b'Conservation'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'historyofdesign', b'History of Design'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture')))])),
                ('feed_image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio.', null=True)),
                ('social_image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page', models.Model),
        ),
        migrations.CreateModel(
            name='PathwayPageAd',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('ad', models.ForeignKey(related_name='+', to='rca.Advert', help_text=b'')),
                ('page', modelcluster.fields.ParentalKey(related_name='manual_adverts', to='rca.PathwayPage')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PathwayPageCarouselItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('overlay_text', models.CharField(help_text=b'', max_length=255, blank=True)),
                ('link', models.URLField(help_text=b'', verbose_name=b'External link', blank=True)),
                ('embedly_url', models.URLField(help_text=b'', verbose_name=b'Vimeo URL', blank=True)),
                ('image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'', null=True)),
                ('link_page', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='wagtailcore.Page', help_text=b'', null=True)),
                ('page', modelcluster.fields.ParentalKey(related_name='carousel_items', to='rca.PathwayPage')),
                ('poster_image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'', null=True)),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PathwayPageImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('image', models.ForeignKey(related_name='+', blank=True, to='rca.RcaImage', help_text=b'', null=True)),
                ('page', modelcluster.fields.ParentalKey(related_name='images', to='rca.PathwayPage')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PathwayPageQuotation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('quotation', models.TextField(help_text=b'')),
                ('quotee', models.CharField(help_text=b'', max_length=255, blank=True)),
                ('quotee_job_title', models.CharField(help_text=b'', max_length=255, blank=True)),
                ('page', modelcluster.fields.ParentalKey(related_name='quotations', to='rca.PathwayPage')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PathwayPageRelatedDocument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('document_name', models.CharField(help_text=b'', max_length=255)),
                ('document', models.ForeignKey(related_name='+', blank=True, to='wagtaildocs.Document', help_text=b'', null=True)),
                ('page', modelcluster.fields.ParentalKey(related_name='documents', to='rca.PathwayPage')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PathwayPageRelatedLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('link_external', models.URLField(help_text=b'', verbose_name=b'External link', blank=True)),
                ('link_text', models.CharField(help_text=b'Link title (or leave blank to use page title', max_length=255, blank=True)),
                ('link', models.ForeignKey(related_name='+', blank=True, to='wagtailcore.Page', help_text=b'', null=True)),
                ('page', modelcluster.fields.ParentalKey(related_name='related_links', to='rca.PathwayPage')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PathwayPageReusableTextSnippet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('page', modelcluster.fields.ParentalKey(related_name='reusable_text_snippets', to='rca.PathwayPage')),
                ('reusable_text_snippet', models.ForeignKey(related_name='+', to='rca.ReusableTextSnippet', help_text=b'')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PathwayPageTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content_object', modelcluster.fields.ParentalKey(related_name='tagged_items', to='rca.PathwayPage')),
                ('tag', models.ForeignKey(related_name='rca_pathwaypagetag_items', to='taggit.Tag')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='pathwaypage',
            name='tags',
            field=modelcluster.contrib.taggit.ClusterTaggableManager(to='taggit.Tag', through='rca.PathwayPageTag', blank=True, help_text=b'', verbose_name='Tags'),
        ),
    ]
