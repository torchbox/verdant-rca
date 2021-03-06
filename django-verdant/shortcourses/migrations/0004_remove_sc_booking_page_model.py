# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2020-08-03 10:48
from __future__ import unicode_literals

from django.db import migrations, models
import wagtail.wagtailcore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0029_unicode_slugfield_dj19'),
        ('rca', '0109_remove-student-char-limits'),
        ('wagtailsearchpromotions', '0002_capitalizeverbose'),
        ('wagtailredirects', '0005_capitalizeverbose'),
        ('wagtailforms', '0003_capitalizeverbose'),
        ('shortcourses', '0003_add_shortcourse_booking_link'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shortcoursebookingpage',
            name='page_ptr',
        ),
        migrations.RemoveField(
            model_name='shortcoursebookingpage',
            name='social_image',
        ),
        migrations.RemoveField(
            model_name='shortcoursepage',
            name='booking_disabled_text',
        ),
        migrations.RemoveField(
            model_name='shortcoursepage',
            name='booking_enabled',
        ),
        migrations.AlterField(
            model_name='shortcoursepage',
            name='ap_course_id',
            field=models.CharField(blank=True, help_text=b'Course ID from the Access Planit booking system. This allows the inclusion of enquiry links.', max_length=8),
        ),
        migrations.AlterField(
            model_name='shortcoursepage',
            name='details',
            field=wagtail.wagtailcore.fields.RichTextField(help_text=b'Course details such as dates, duration, location and fee. Enquiry links will be appended to this.', null=True),
        ),
        migrations.DeleteModel(
            name='ShortCourseBookingPage',
        ),
    ]
