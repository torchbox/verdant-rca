# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.contrib.taggit
import modelcluster.fields
import wagtail.wagtailcore.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('wagtaildocs', '0007_merge'),
        ('wagtailcore', '0029_unicode_slugfield_dj19'),
        ('taggit', '0002_auto_20150616_2121'),
        ('rca', '0093_auto_20180808_1231'),
        ('taxonomy', '0022_degreelevel'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShortCourseAd',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('ad', models.ForeignKey(help_text=b'', on_delete=django.db.models.deletion.CASCADE, related_name='+', to='rca.Advert')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShortCourseCarouselItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('overlay_text', models.CharField(blank=True, help_text=b'', max_length=255)),
                ('link', models.URLField(blank=True, help_text=b'', verbose_name=b'External link')),
                ('embedly_url', models.URLField(blank=True, help_text=b'', verbose_name=b'Vimeo URL')),
                ('image', models.ForeignKey(blank=True, help_text=b'', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='rca.RcaImage')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShortCourseImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('image', models.ForeignKey(blank=True, help_text=b'', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='rca.RcaImage')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShortCoursePage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('collapse_upcoming_events', models.BooleanField(default=False, help_text=b'')),
                ('social_text', models.CharField(blank=True, help_text=b'', max_length=255)),
                ('intro', wagtail.wagtailcore.fields.RichTextField(blank=True, help_text=b'')),
                ('body', wagtail.wagtailcore.fields.RichTextField(help_text=b'')),
                ('strapline', models.CharField(blank=True, help_text=b'', max_length=255)),
                ('middle_column_body', wagtail.wagtailcore.fields.RichTextField(blank=True, help_text=b'')),
                ('show_on_homepage', models.BooleanField(default=False, help_text=b'')),
                ('twitter_feed', models.CharField(blank=True, help_text=b'Replace the default Twitter feed by providing an alternative Twitter handle (without the @ symbol)', max_length=255)),
                ('show_on_school_page', models.BooleanField(default=False, help_text=b'')),
                ('programme_finder_exclude', models.BooleanField(default=False, help_text=b'Tick to exclude this page from the programme finder.', verbose_name=b'Exclude from programme finder')),
                ('degree_level', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='degree_shortcourse_pages', to='taxonomy.DegreeLevel')),
                ('feed_image', models.ForeignKey(blank=True, help_text=b'The image displayed in content feeds, such as the news carousel. Should be 16:9 ratio.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='rca.RcaImage')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page', models.Model),
        ),
        migrations.CreateModel(
            name='ShortCoursePageKeyword',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_object', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, to='shortcourses.ShortCoursePage')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shortcourses_shortcoursepagekeyword_items', to='taggit.Tag')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShortCourseQuotation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('quotation', models.TextField(help_text=b'')),
                ('quotee', models.CharField(blank=True, help_text=b'', max_length=255)),
                ('quotee_job_title', models.CharField(blank=True, help_text=b'', max_length=255)),
                ('page', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='shortcourse_quotations', to='shortcourses.ShortCoursePage')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShortCourseRelatedDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('document_name', models.CharField(help_text=b'', max_length=255)),
                ('document', models.ForeignKey(blank=True, help_text=b'', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='wagtaildocs.Document')),
                ('page', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='shortcourse_documents', to='shortcourses.ShortCoursePage')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShortCourseRelatedLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('link_external', models.URLField(blank=True, help_text=b'', verbose_name=b'External link')),
                ('link_text', models.CharField(blank=True, help_text=b'Link title (or leave blank to use page title)', max_length=255)),
                ('link', models.ForeignKey(blank=True, help_text=b'', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='wagtailcore.Page')),
                ('page', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='shortcourse_related_links', to='shortcourses.ShortCoursePage')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShortCourseReusableTextSnippet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('page', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='shortcourse_reusable_text_snippets', to='shortcourses.ShortCoursePage')),
                ('reusable_text_snippet', models.ForeignKey(help_text=b'', on_delete=django.db.models.deletion.CASCADE, related_name='+', to='rca.ReusableTextSnippet')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShortCourseTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_object', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='tagged_items', to='shortcourses.ShortCoursePage')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shortcourses_shortcoursetag_items', to='taggit.Tag')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='shortcoursepage',
            name='programme_finder_keywords',
            field=modelcluster.contrib.taggit.ClusterTaggableManager(blank=True, help_text=b'A comma-separated list of keywords.', through='shortcourses.ShortCoursePageKeyword', to='taggit.Tag', verbose_name=b'Keywords'),
        ),
        migrations.AddField(
            model_name='shortcoursepage',
            name='related_area',
            field=models.ForeignKey(blank=True, help_text=b'', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shortcourses', to='taxonomy.Area'),
        ),
        migrations.AddField(
            model_name='shortcoursepage',
            name='related_programme',
            field=models.ForeignKey(blank=True, help_text=b'', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shortcourses', to='taxonomy.Programme'),
        ),
        migrations.AddField(
            model_name='shortcoursepage',
            name='related_school',
            field=models.ForeignKey(help_text=b'', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shortcourses', to='taxonomy.School', verbose_name=b'School'),
        ),
        migrations.AddField(
            model_name='shortcoursepage',
            name='social_image',
            field=models.ForeignKey(blank=True, help_text=b'', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='rca.RcaImage'),
        ),
        migrations.AddField(
            model_name='shortcoursepage',
            name='tags',
            field=modelcluster.contrib.taggit.ClusterTaggableManager(blank=True, help_text=b'Use the "student-story" or "alumni-story" tags to make this page appear in the homepage packery (if "Show on homepage" is ticked too).', through='shortcourses.ShortCourseTag', to='taggit.Tag', verbose_name='Tags'),
        ),
        migrations.AddField(
            model_name='shortcourseimage',
            name='page',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='shortcourse_images', to='shortcourses.ShortCoursePage'),
        ),
        migrations.AddField(
            model_name='shortcoursecarouselitem',
            name='link_page',
            field=models.ForeignKey(blank=True, help_text=b'', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailcore.Page'),
        ),
        migrations.AddField(
            model_name='shortcoursecarouselitem',
            name='page',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='shortcourse_carousel_items', to='shortcourses.ShortCoursePage'),
        ),
        migrations.AddField(
            model_name='shortcoursecarouselitem',
            name='poster_image',
            field=models.ForeignKey(blank=True, help_text=b'', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='rca.RcaImage'),
        ),
        migrations.AddField(
            model_name='shortcoursead',
            name='page',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='shortcourse_manual_adverts', to='shortcourses.ShortCoursePage'),
        ),
    ]
