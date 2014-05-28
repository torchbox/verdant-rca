from django.core.management.base import BaseCommand
from django.db import models
from django.conf import settings
from rca.models import NewStudentPage
from rca.report_generator import Report
import csv
from zipfile import ZipFile
import os


def get_profile_image_zip_filename(student):
    return '-'.join([
        student.first_name.replace(' ', '-'),
        student.last_name.replace(' ', '-'),
        str(student.id),
    ]) + os.path.splitext(student.profile_image.file.name)[1]


class ProfileImageDumpReport(Report):
    def first_name_field(self, student):
        return student[0], None, None

    def last_name_field(self, student):
        return student[1], None, None

    def programme_field(self, student):
        return student[2], None, None

    def page_field(self, student):
        page = student[4]

        if page:
            return (
                page.title,
                None,
                'http://www.rca.ac.uk/admin/pages/' + str(page.id) + '/edit/',
            )
        else:
            return (
                "Not found",
                'error',
                None,
            )

    def profile_image_field(self, student):
        page = student[4]

        if page:
            if page.profile_image:
                filename = get_profile_image_zip_filename(page)
                return (
                    filename,
                    None,
                    'images/' + filename,
                )
            else:
                return (
                    "Not set",
                    'error',
                    None,
                )
        else:
            return (
                "",
                None,
                None,
            )

    def profile_image_width_field(self, student):
        page = student[4]

        if page and page.profile_image:
            return (
                str(page.profile_image.width),
                None,
                None,
            )
        else:
            return (
                "",
                None,
                None,
            )

    def profile_image_height_field(self, student):
        page = student[4]

        if page and page.profile_image:
            return (
                str(page.profile_image.height),
                None,
                None,
            )
        else:
            return (
                "",
                'error',
                None,
            )

    title = "Students report"

    fields = (
        ("First Name", first_name_field),
        ("Last Name", last_name_field),
        ("Programme", programme_field),
        ("Page", page_field),
        ("Profile image", profile_image_field),
        ("Width (px)", profile_image_width_field),
        ("Height (px)", profile_image_height_field),
    )

    extra_css = """
        td.error {
            color: #FF0000;
            font-weight: bold;
        }
        """


class Command(BaseCommand):
    def process_student(self, student):
        # Student info
        programme = student[0]
        first_name = student[2]
        last_name = student[1]
        email = student[3]

        # Get list of possible pages
        students = NewStudentPage.objects.all()

        # Find student page
        page = None

        # Find by email
        if page is None and email:
            page = students.filter(emails__email=email).first()

        # Find by owner email
        if page is None and email:
            page = students.filter(owner__email=email).first()

        # Find by name
        if page is None:
            page = students.filter(last_name__iexact=last_name, first_name__iexact=first_name).first()

        return first_name, last_name, programme, email, page

    def handle(self, filename, **options):
        # Get list of students
        students = []
        with open(filename) as f:
            for student in csv.reader(f):
                students.append(self.process_student(student))

        # Create zipfile
        with ZipFile('profile_image_dump.zip', 'w') as zf:
            # Add profile images into zip
            for student in students:
                page = student[4]
                if page and page.profile_image:
                    filename = page.profile_image.file.name

                    try:
                        zf.write(os.path.join(settings.MEDIA_ROOT, filename), 'images/' + get_profile_image_zip_filename(page))
                    except (IOError, OSError) as e:
                        print e

            # Generate report
            report = ProfileImageDumpReport(students)
            zf.writestr('report.html', report.get_html())
            zf.writestr('report.csv', report.get_csv())
