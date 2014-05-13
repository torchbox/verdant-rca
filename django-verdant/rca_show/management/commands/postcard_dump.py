"""
This script checks through all students of a particular year and
puts all of their postcard images into a zip file with a report
"""
from django.core.management.base import BaseCommand
from django.db import models
from rca.models import NewStudentPage
from rca.report_generator import Report
from PIL import Image
from zipfile import ZipFile
import os


class PostcardDumpReport(Report):
    def name_field(self, student):
        return (
            student.title,
            None,
            'http://www.rca.ac.uk/admin/pages/' + str(student.id) + '/edit/',
        )

    def get_image(self, image):
        if image:
            # Work out image mode
            try:
                img = Image.open(image.file.file)
                image_mode = img.mode
            except IOError:
                image_mode = "Unknown"

            return (
                "Yes (" + str(image.width) + "x" + str(image.height) + " " + image_mode + ")",
                None,
                'images/' + os.path.split(image.file.name)[1],
            )
        else:
            return (
                "No",
                'error',
                None,
            )

    def postcard_image_field(self, student):
        return self.get_image(student.postcard_image)

    title = "Postcard image dump"

    fields = (
        ("Name", name_field),
        ("Postcard image", postcard_image_field),
    )

    extra_css = """
        td.error {
            color: #FF0000;
            font-weight: bold;
        }
        """


class Command(BaseCommand):
    def students_for_year(self, year):
        q = models.Q(ma_graduation_year=year) | models.Q(mphil_graduation_year=year) | models.Q(phd_graduation_year=year)
        return NewStudentPage.objects.filter(q)

    def handle(self, year, **options):
        # Get students
        students = self.students_for_year(year).order_by('phd_programme', 'mphil_programme', 'ma_programme', 'title')

        # Create zipfile
        with ZipFile('postcard_dump.zip', 'w') as zf:
            # Add postcard images into zip
            for student in students:
                if student.postcard_image:
                    filename = student.postcard_image.file.name

                    try:
                        zf.write(filename, 'images/' + os.path.split(filename)[1])
                    except (IOError, OSError):
                        pass

            # Generate report
            report = PostcardDumpReport(students)
            zf.writestr('report.html', report.get_html().encode('UTF-8'))
