# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wagtail.wagtailcore.fields
import modelcluster.fields
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rca', '0001_initial'),
        ('wagtailcore', '0010_change_page_owner_to_null_on_delete'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShowExhibitionMapIndex',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('social_text', models.CharField(help_text=b'', max_length=255, blank=True)),
                ('social_image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page', models.Model),
        ),
        migrations.CreateModel(
            name='ShowExhibitionMapIndexContent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('body', wagtail.wagtailcore.fields.RichTextField(blank=True)),
                ('map_coords', models.CharField(help_text=b'Lat lon coordinates for centre of map e.g 51.501533, -0.179284', max_length=255, blank=True)),
                ('page', modelcluster.fields.ParentalKey(related_name='content_block', to='rca_show.ShowExhibitionMapIndex')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ShowExhibitionMapPage',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('social_text', models.CharField(help_text=b'', max_length=255, blank=True)),
                ('body', wagtail.wagtailcore.fields.RichTextField(blank=True)),
                ('campus', models.CharField(blank=True, max_length=255, null=True, choices=[(b'kensington', b'Kensington'), (b'battersea', b'Battersea')])),
                ('social_image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page', models.Model),
        ),
        migrations.CreateModel(
            name='ShowIndexPage',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('social_text', models.CharField(help_text=b'', max_length=255, blank=True)),
                ('body', wagtail.wagtailcore.fields.RichTextField(help_text=b'Optional body text. Useful for holding pages prior to Show launch.', blank=True)),
                ('year', models.CharField(max_length=4, blank=True)),
                ('overlay_intro', wagtail.wagtailcore.fields.RichTextField(blank=True)),
                ('exhibition_date', models.TextField(max_length=255, blank=True)),
                ('password_prompt', models.CharField(help_text=b'A custom message asking the user to log in, on protected pages', max_length=255, blank=True)),
                ('parent_show_index', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca_show.ShowIndexPage', null=True)),
                ('social_image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page', models.Model),
        ),
        migrations.CreateModel(
            name='ShowIndexPageCarouselItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('overlay_text', models.CharField(help_text=b'', max_length=255, blank=True)),
                ('link', models.URLField(help_text=b'', verbose_name=b'External link', blank=True)),
                ('embedly_url', models.URLField(help_text=b'', verbose_name=b'Vimeo URL', blank=True)),
                ('image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'', null=True)),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ShowIndexPageProgramme',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('programme', models.CharField(max_length=255, choices=[(b'2015', ((b'animation', b'Animation'), (b'architecture', b'Architecture'), (b'ceramicsglass', b'Ceramics & Glass'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'criticalwritinginartdesign', b'Critical Writing in Art & Design'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'designinteractions', b'Design Interactions'), (b'designproducts', b'Design Products'), (b'fashionmenswear', b'Fashion Menswear'), (b'fashionwomenswear', b'Fashion Womenswear'), (b'globalinnovationdesign', b'Global Innovation Design'), (b'historyofdesign', b'History of Design'), (b'informationexperiencedesign', b'Information Experience Design'), (b'innovationdesignengineering', b'Innovation Design Engineering'), (b'interiordesign', b'Interior Design'), (b'jewelleryandmetal', b'Jewellery & Metal'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'), (b'servicedesign', b'Service Design'), (b'textiles', b'Textiles'), (b'vehicledesign', b'Vehicle Design'), (b'visualcommunication', b'Visual Communication'))), (b'2014', ((b'animation', b'Animation'), (b'architecture', b'Architecture'), (b'ceramicsglass', b'Ceramics & Glass'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'criticalwritinginartdesign', b'Critical Writing in Art & Design'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'designinteractions', b'Design Interactions'), (b'designproducts', b'Design Products'), (b'fashionmenswear', b'Fashion Menswear'), (b'fashionwomenswear', b'Fashion Womenswear'), (b'globalinnovationdesign', b'Global Innovation Design'), (b'goldsmithingsilversmithingmetalworkjewellery', b'Goldsmithing, Silversmithing, Metalwork & Jewellery'), (b'historyofdesign', b'History of Design'), (b'informationexperiencedesign', b'Information Experience Design'), (b'innovationdesignengineering', b'Innovation Design Engineering'), (b'interiordesign', b'Interior Design'), (b'jewelleryandmetal', b'Jewellery & Metal'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'), (b'servicedesign', b'Service Design'), (b'textiles', b'Textiles'), (b'vehicledesign', b'Vehicle Design'), (b'visualcommunication', b'Visual Communication'))), (b'2013', ((b'animation', b'Animation'), (b'architecture', b'Architecture'), (b'ceramicsglass', b'Ceramics & Glass'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'criticalwritinginartdesign', b'Critical Writing in Art & Design'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'designinteractions', b'Design Interactions'), (b'designproducts', b'Design Products'), (b'fashionmenswear', b'Fashion Menswear'), (b'fashionwomenswear', b'Fashion Womenswear'), (b'goldsmithingsilversmithingmetalworkjewellery', b'Goldsmithing, Silversmithing, Metalwork & Jewellery'), (b'historyofdesign', b'History of Design'), (b'innovationdesignengineering', b'Innovation Design Engineering'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'), (b'servicedesign', b'Service Design'), (b'textiles', b'Textiles'), (b'vehicledesign', b'Vehicle Design'), (b'visualcommunication', b'Visual Communication'))), (b'2012', ((b'animation', b'Animation'), (b'architecture', b'Architecture'), (b'ceramicsglass', b'Ceramics & Glass'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'criticalwritinginartdesign', b'Critical Writing in Art & Design'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'designinteractions', b'Design Interactions'), (b'designproducts', b'Design Products'), (b'fashionmenswear', b'Fashion Menswear'), (b'fashionwomenswear', b'Fashion Womenswear'), (b'goldsmithingsilversmithingmetalworkjewellery', b'Goldsmithing, Silversmithing, Metalwork & Jewellery'), (b'historyofdesign', b'History of Design'), (b'innovationdesignengineering', b'Innovation Design Engineering'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'), (b'textiles', b'Textiles'), (b'vehicledesign', b'Vehicle Design'), (b'visualcommunication', b'Visual Communication'))), (b'2011', ((b'animation', b'Animation'), (b'architecture', b'Architecture'), (b'ceramicsglass', b'Ceramics & Glass'), (b'communicationartdesign', b'Communication Art & Design'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'criticalwritinginartdesign', b'Critical Writing in Art & Design'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'designinteractions', b'Design Interactions'), (b'designproducts', b'Design Products'), (b'fashionmenswear', b'Fashion Menswear'), (b'fashionwomenswear', b'Fashion Womenswear'), (b'goldsmithingsilversmithingmetalworkjewellery', b'Goldsmithing, Silversmithing, Metalwork & Jewellery'), (b'historyofdesign', b'History of Design'), (b'innovationdesignengineering', b'Innovation Design Engineering'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'), (b'textiles', b'Textiles'), (b'vehicledesign', b'Vehicle Design'))), (b'2010', ((b'animation', b'Animation'), (b'architecture', b'Architecture'), (b'ceramicsglass', b'Ceramics & Glass'), (b'communicationartdesign', b'Communication Art & Design'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'criticalwritinginartdesign', b'Critical Writing in Art & Design'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'designinteractions', b'Design Interactions'), (b'designproducts', b'Design Products'), (b'fashionmenswear', b'Fashion Menswear'), (b'fashionwomenswear', b'Fashion Womenswear'), (b'goldsmithingsilversmithingmetalworkjewellery', b'Goldsmithing, Silversmithing, Metalwork & Jewellery'), (b'historyofdesign', b'History of Design'), (b'innovationdesignengineering', b'Innovation Design Engineering'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'), (b'textiles', b'Textiles'), (b'vehicledesign', b'Vehicle Design'))), (b'2009', ((b'animation', b'Animation'), (b'communicationartdesign', b'Communication Art & Design'), (b'conservation', b'Conservation'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'historyofdesign', b'History of Design'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'))), (b'2008', ((b'animation', b'Animation'), (b'communicationartdesign', b'Communication Art & Design'), (b'conservation', b'Conservation'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'historyofdesign', b'History of Design'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'))), (b'2007', ((b'animation', b'Animation'), (b'communicationartdesign', b'Communication Art & Design'), (b'conservation', b'Conservation'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'historyofdesign', b'History of Design'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture')))])),
                ('page', modelcluster.fields.ParentalKey(related_name='programmes', to='rca_show.ShowIndexPage')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ShowIndexProgrammeIntro',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('programme', models.CharField(max_length=255, choices=[(b'2015', ((b'animation', b'Animation'), (b'architecture', b'Architecture'), (b'ceramicsglass', b'Ceramics & Glass'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'criticalwritinginartdesign', b'Critical Writing in Art & Design'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'designinteractions', b'Design Interactions'), (b'designproducts', b'Design Products'), (b'fashionmenswear', b'Fashion Menswear'), (b'fashionwomenswear', b'Fashion Womenswear'), (b'globalinnovationdesign', b'Global Innovation Design'), (b'historyofdesign', b'History of Design'), (b'informationexperiencedesign', b'Information Experience Design'), (b'innovationdesignengineering', b'Innovation Design Engineering'), (b'interiordesign', b'Interior Design'), (b'jewelleryandmetal', b'Jewellery & Metal'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'), (b'servicedesign', b'Service Design'), (b'textiles', b'Textiles'), (b'vehicledesign', b'Vehicle Design'), (b'visualcommunication', b'Visual Communication'))), (b'2014', ((b'animation', b'Animation'), (b'architecture', b'Architecture'), (b'ceramicsglass', b'Ceramics & Glass'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'criticalwritinginartdesign', b'Critical Writing in Art & Design'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'designinteractions', b'Design Interactions'), (b'designproducts', b'Design Products'), (b'fashionmenswear', b'Fashion Menswear'), (b'fashionwomenswear', b'Fashion Womenswear'), (b'globalinnovationdesign', b'Global Innovation Design'), (b'goldsmithingsilversmithingmetalworkjewellery', b'Goldsmithing, Silversmithing, Metalwork & Jewellery'), (b'historyofdesign', b'History of Design'), (b'informationexperiencedesign', b'Information Experience Design'), (b'innovationdesignengineering', b'Innovation Design Engineering'), (b'interiordesign', b'Interior Design'), (b'jewelleryandmetal', b'Jewellery & Metal'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'), (b'servicedesign', b'Service Design'), (b'textiles', b'Textiles'), (b'vehicledesign', b'Vehicle Design'), (b'visualcommunication', b'Visual Communication'))), (b'2013', ((b'animation', b'Animation'), (b'architecture', b'Architecture'), (b'ceramicsglass', b'Ceramics & Glass'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'criticalwritinginartdesign', b'Critical Writing in Art & Design'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'designinteractions', b'Design Interactions'), (b'designproducts', b'Design Products'), (b'fashionmenswear', b'Fashion Menswear'), (b'fashionwomenswear', b'Fashion Womenswear'), (b'goldsmithingsilversmithingmetalworkjewellery', b'Goldsmithing, Silversmithing, Metalwork & Jewellery'), (b'historyofdesign', b'History of Design'), (b'innovationdesignengineering', b'Innovation Design Engineering'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'), (b'servicedesign', b'Service Design'), (b'textiles', b'Textiles'), (b'vehicledesign', b'Vehicle Design'), (b'visualcommunication', b'Visual Communication'))), (b'2012', ((b'animation', b'Animation'), (b'architecture', b'Architecture'), (b'ceramicsglass', b'Ceramics & Glass'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'criticalwritinginartdesign', b'Critical Writing in Art & Design'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'designinteractions', b'Design Interactions'), (b'designproducts', b'Design Products'), (b'fashionmenswear', b'Fashion Menswear'), (b'fashionwomenswear', b'Fashion Womenswear'), (b'goldsmithingsilversmithingmetalworkjewellery', b'Goldsmithing, Silversmithing, Metalwork & Jewellery'), (b'historyofdesign', b'History of Design'), (b'innovationdesignengineering', b'Innovation Design Engineering'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'), (b'textiles', b'Textiles'), (b'vehicledesign', b'Vehicle Design'), (b'visualcommunication', b'Visual Communication'))), (b'2011', ((b'animation', b'Animation'), (b'architecture', b'Architecture'), (b'ceramicsglass', b'Ceramics & Glass'), (b'communicationartdesign', b'Communication Art & Design'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'criticalwritinginartdesign', b'Critical Writing in Art & Design'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'designinteractions', b'Design Interactions'), (b'designproducts', b'Design Products'), (b'fashionmenswear', b'Fashion Menswear'), (b'fashionwomenswear', b'Fashion Womenswear'), (b'goldsmithingsilversmithingmetalworkjewellery', b'Goldsmithing, Silversmithing, Metalwork & Jewellery'), (b'historyofdesign', b'History of Design'), (b'innovationdesignengineering', b'Innovation Design Engineering'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'), (b'textiles', b'Textiles'), (b'vehicledesign', b'Vehicle Design'))), (b'2010', ((b'animation', b'Animation'), (b'architecture', b'Architecture'), (b'ceramicsglass', b'Ceramics & Glass'), (b'communicationartdesign', b'Communication Art & Design'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'criticalwritinginartdesign', b'Critical Writing in Art & Design'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'designinteractions', b'Design Interactions'), (b'designproducts', b'Design Products'), (b'fashionmenswear', b'Fashion Menswear'), (b'fashionwomenswear', b'Fashion Womenswear'), (b'goldsmithingsilversmithingmetalworkjewellery', b'Goldsmithing, Silversmithing, Metalwork & Jewellery'), (b'historyofdesign', b'History of Design'), (b'innovationdesignengineering', b'Innovation Design Engineering'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'), (b'textiles', b'Textiles'), (b'vehicledesign', b'Vehicle Design'))), (b'2009', ((b'animation', b'Animation'), (b'communicationartdesign', b'Communication Art & Design'), (b'conservation', b'Conservation'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'historyofdesign', b'History of Design'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'))), (b'2008', ((b'animation', b'Animation'), (b'communicationartdesign', b'Communication Art & Design'), (b'conservation', b'Conservation'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'historyofdesign', b'History of Design'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture'))), (b'2007', ((b'animation', b'Animation'), (b'communicationartdesign', b'Communication Art & Design'), (b'conservation', b'Conservation'), (b'criticalhistoricalstudies', b'Critical & Historical Studies'), (b'curatingcontemporaryart', b'Curating Contemporary Art'), (b'historyofdesign', b'History of Design'), (b'painting', b'Painting'), (b'photography', b'Photography'), (b'printmaking', b'Printmaking'), (b'sculpture', b'Sculpture')))])),
                ('intro', wagtail.wagtailcore.fields.RichTextField(blank=True)),
                ('page', modelcluster.fields.ParentalKey(related_name='programme_intros', to='rca_show.ShowIndexPage')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ShowStandardPage',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('social_text', models.CharField(help_text=b'', max_length=255, blank=True)),
                ('body', wagtail.wagtailcore.fields.RichTextField(blank=True)),
                ('map_coords', models.CharField(help_text=b'Lat lon coordinates for centre of map e.g 51.501533, -0.179284', max_length=255, blank=True)),
                ('listing_intro', models.CharField(help_text=b'Used only on pages listing news items', max_length=100, blank=True)),
                ('feed_image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio.', null=True)),
                ('social_image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page', models.Model),
        ),
        migrations.CreateModel(
            name='ShowStandardPageCarouselItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('overlay_text', models.CharField(help_text=b'', max_length=255, blank=True)),
                ('link', models.URLField(help_text=b'', verbose_name=b'External link', blank=True)),
                ('embedly_url', models.URLField(help_text=b'', verbose_name=b'Vimeo URL', blank=True)),
                ('image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'', null=True)),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ShowStandardPageContent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('body', wagtail.wagtailcore.fields.RichTextField(blank=True)),
                ('map_coords', models.CharField(help_text=b'Lat lon coordinates for centre of map e.g 51.501533, -0.179284', max_length=255, blank=True)),
                ('page', modelcluster.fields.ParentalKey(related_name='content_block', to='rca_show.ShowStandardPage')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ShowStreamPage',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('social_text', models.CharField(help_text=b'', max_length=255, blank=True)),
                ('body', wagtail.wagtailcore.fields.RichTextField(blank=True)),
                ('poster_image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', null=True)),
                ('social_image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page', models.Model),
        ),
        migrations.CreateModel(
            name='ShowStreamPageCarouselItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sort_order', models.IntegerField(null=True, editable=False, blank=True)),
                ('overlay_text', models.CharField(help_text=b'', max_length=255, blank=True)),
                ('link', models.URLField(help_text=b'', verbose_name=b'External link', blank=True)),
                ('embedly_url', models.URLField(help_text=b'', verbose_name=b'Vimeo URL', blank=True)),
                ('image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'', null=True)),
                ('link_page', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='wagtailcore.Page', help_text=b'', null=True)),
                ('page', modelcluster.fields.ParentalKey(related_name='carousel_items', to='rca_show.ShowStreamPage')),
                ('poster_image', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'', null=True)),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='showstandardpagecarouselitem',
            name='link_page',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='wagtailcore.Page', help_text=b'', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='showstandardpagecarouselitem',
            name='page',
            field=modelcluster.fields.ParentalKey(related_name='carousel_items', to='rca_show.ShowStandardPage'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='showstandardpagecarouselitem',
            name='poster_image',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='showindexpagecarouselitem',
            name='link_page',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='wagtailcore.Page', help_text=b'', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='showindexpagecarouselitem',
            name='page',
            field=modelcluster.fields.ParentalKey(related_name='carousel_items', to='rca_show.ShowIndexPage'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='showindexpagecarouselitem',
            name='poster_image',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='rca.RcaImage', help_text=b'', null=True),
            preserve_default=True,
        ),
    ]
