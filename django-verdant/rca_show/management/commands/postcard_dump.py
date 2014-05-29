"""
This script checks through all students of a particular year and
puts all of their postcard images into a zip file with a report
"""
from django.core.management.base import BaseCommand
from django.db import models
from django.conf import settings
from rca.models import NewStudentPage
from rca.report_generator import Report
from PIL import Image
from zipfile import ZipFile
from optparse import make_option
import humanize
import os


def get_postcard_zip_filename(student):
    return '-'.join([
        str(student.id),
        student.first_name.replace(' ', '-'),
        student.last_name.replace(' ', '-'),
    ]) + os.path.splitext(student.postcard_image.file.name)[1]


class PostcardDumpReport(Report):
    def student_name_field(self, student):
        return (
            student.title,
            None,
            'http://www.rca.ac.uk/admin/pages/' + str(student.id) + '/edit/',
        )

    def page_status_field(self, student):
        status = student.status_string.upper()

        # If page in moderation
        if student.get_latest_revision().submitted_for_moderation:
            status += " (in moderation)"

        return (
            status,
            'error' if not student.live else None,
            None,
        )

    def page_in_moderation_field(self, student):
        return (
            "Yes" if student.get_latest_revision().submitted_for_moderation else "No",
            None,
            None,
        )

    def student_fname_field(self, student):
        return (
            student.first_name or "Not set",
            'error' if not student.first_name else None,
            None,
        )

    def student_lname_field(self, student):
        return (
            student.last_name or "Not set",
            'error' if not student.last_name else None,
            None,
        )

    def student_degree_field(self, student):
        profile = student.get_profile()

        if profile is not None:
            return (
                profile['name'] or "Not set",
                'error' if not profile['name'] else None,
                None,
            )
        else:
            return (
                "Not set",
                'error',
                None,
            )

    title = "Postcard image dump"

    fields = (
        ("Name", student_name_field),
        ("Page Status", page_status_field),
        ("First name", student_fname_field),
        ("Last name", student_lname_field),
        ("Degree level", student_degree_field),

        ("Programme", student_programme_field),
        ("Specialism", student_specialism_field),
        ("Email", student_email_field),
        ("Phone", student_phone_number_field),
        ("Website", student_website_field),
        ("Carousel items", student_carousel_items_field),
        ("Image", image_field),
        ("Image File Size", file_size_field),
        ("Image Width", width_field),
        ("Image Height", height_field),
        ("Image Colour Format", colour_format_field),
        ("Image Caption", caption_field),
        ("Image Permission", permission_field),
    )

    extra_css = """
        td, th {
            padding: 1px;
            font-size: 0.8em;
        }
        td.error {
            color: #FF0000;
            font-weight: bold;
        }
        """


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--no-fashion',
            action='store_true',
            dest='no_fashion',
            default=False,
            help='Remove fashion students from dump'),
        make_option('--exclude',
            action='store',
            type='string',
            dest='exclude',
            default=None,
            help='Filename with list of student IDs to exclude from this report'),
        )

    def students_for_year(self, year):
        q = models.Q(ma_graduation_year=year) | models.Q(mphil_graduation_year=year) | models.Q(phd_graduation_year=year)
        return NewStudentPage.objects.filter(q)

    def handle(self, year, **options):
        # Get students
        students = self.students_for_year(year).order_by('phd_programme', 'mphil_programme', 'ma_programme', 'last_name', 'first_name')

        # Remove fashion students if '--no-fashion' option was used
        if options['no_fashion']:
            fashion_q = models.Q(phd_programme='fashionmenswear') | models.Q(phd_programme='fashionwomenswear') | \
                        models.Q(mphil_programme='fashionmenswear') | models.Q(mphil_programme='fashionwomenswear') | \
                        models.Q(ma_programme='fashionmenswear') | models.Q(ma_programme='fashionwomenswear')
            students = students.exclude(fashion_q)

        # Remove any excluded students
        if options['exclude'] is not None:
            excluded_students = []
            with open(options['exclude']) as f:
                for student_id in f:
                    try:
                        excluded_students.append(int(student_id))
                    except (TypeError, ValueError):
                        print "WARN: '" + str(student_id) + "' is not an integer!"

            print excluded_students
            students = students.exclude(id__in=excluded_students)

        # Create zipfile
        with ZipFile('postcard_dump.zip', 'w') as zf:
            # Add postcard images into zip
            for student in students:
                if student.postcard_image:
                    filename = student.postcard_image.file.name

                    try:
                        zf.write(os.path.join(settings.MEDIA_ROOT, filename), 'images/' + get_postcard_zip_filename(student))
                    except (IOError, OSError) as e:
                        print e

            # Generate report
            report = PostcardDumpReport(students)
            report.run()
            zf.writestr('report.html', report.get_html())
            zf.writestr('report.csv', report.get_csv())
