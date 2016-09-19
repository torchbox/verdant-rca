# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailredirects', '0004_set_unique_on_path_and_site'),
        ('wagtailcore', '0020_add_index_on_page_first_published_at'),
        ('wagtailforms', '0002_add_verbose_names'),
        ('wagtailsearchpromotions', '0001_initial'),
        ('rca', '0038_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentpage',
            name='feed_image',
        ),
        migrations.RemoveField(
            model_name='studentpage',
            name='page_ptr',
        ),
        migrations.RemoveField(
            model_name='studentpage',
            name='profile_image',
        ),
        migrations.RemoveField(
            model_name='studentpage',
            name='social_image',
        ),
        migrations.RemoveField(
            model_name='studentpageawards',
            name='page',
        ),
        migrations.RemoveField(
            model_name='studentpagecarouselitem',
            name='image',
        ),
        migrations.RemoveField(
            model_name='studentpagecarouselitem',
            name='link_page',
        ),
        migrations.RemoveField(
            model_name='studentpagecarouselitem',
            name='page',
        ),
        migrations.RemoveField(
            model_name='studentpagecarouselitem',
            name='poster_image',
        ),
        migrations.RemoveField(
            model_name='studentpageconference',
            name='page',
        ),
        migrations.RemoveField(
            model_name='studentpagecontactsemail',
            name='page',
        ),
        migrations.RemoveField(
            model_name='studentpagecontactsphone',
            name='page',
        ),
        migrations.RemoveField(
            model_name='studentpagecontactswebsite',
            name='page',
        ),
        migrations.RemoveField(
            model_name='studentpagedegree',
            name='page',
        ),
        migrations.RemoveField(
            model_name='studentpageexhibition',
            name='page',
        ),
        migrations.RemoveField(
            model_name='studentpageexperience',
            name='page',
        ),
        migrations.RemoveField(
            model_name='studentpagepublication',
            name='page',
        ),
        migrations.RemoveField(
            model_name='studentpagesupervisor',
            name='page',
        ),
        migrations.RemoveField(
            model_name='studentpagesupervisor',
            name='supervisor',
        ),
        migrations.RemoveField(
            model_name='studentpageworkcollaborator',
            name='page',
        ),
        migrations.RemoveField(
            model_name='studentpageworksponsor',
            name='page',
        ),
        migrations.DeleteModel(
            name='StudentPage',
        ),
        migrations.DeleteModel(
            name='StudentPageAwards',
        ),
        migrations.DeleteModel(
            name='StudentPageCarouselItem',
        ),
        migrations.DeleteModel(
            name='StudentPageConference',
        ),
        migrations.DeleteModel(
            name='StudentPageContactsEmail',
        ),
        migrations.DeleteModel(
            name='StudentPageContactsPhone',
        ),
        migrations.DeleteModel(
            name='StudentPageContactsWebsite',
        ),
        migrations.DeleteModel(
            name='StudentPageDegree',
        ),
        migrations.DeleteModel(
            name='StudentPageExhibition',
        ),
        migrations.DeleteModel(
            name='StudentPageExperience',
        ),
        migrations.DeleteModel(
            name='StudentPagePublication',
        ),
        migrations.DeleteModel(
            name='StudentPageSupervisor',
        ),
        migrations.DeleteModel(
            name='StudentPageWorkCollaborator',
        ),
        migrations.DeleteModel(
            name='StudentPageWorkSponsor',
        ),
    ]
