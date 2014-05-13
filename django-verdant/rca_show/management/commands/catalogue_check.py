"""
This script checks through all students of a particular year and makes the following checks:
 - Name, programme, email and phone number has been filled in
 - Have profile images and postcard images have been set and are above a minumum size
 - Have at least one carousel item

It outputs a report of the above in HTML and CSV format
"""
from django.core.management.base import BaseCommand
from django.db import models
from rca.models import NewStudentPage
from rca.report_generator import Report
from PIL import Image


class CatalogueCheckReport(Report):
    def name_field(self, student):
        return (
            student.title,
            None,
            'http://www.rca.ac.uk/admin/pages/' + str(student.id) + '/edit/',
        )

    def page_status_field(self, student):
        return (
            "LIVE" if student.live else "DRAFT",
            'error' if not student.live else None,
            None,
        )

    def programme_field(self, student):
        return (
            student.get_profile()['programme_display'] or "Not set",
            'error' if not student.programme else None,
            None,
        )

    def get_child_objects(self, child_objects):
        has_child_objects = child_objects.exists()
        return (
            "Yes" if has_child_objects else "No",
            'error' if not has_child_objects else None,
            None,
        )

    def email_field(self, student):
        return self.get_child_objects(student.emails)

    def phone_number_field(self, student):
        return self.get_child_objects(student.phones)

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
                'http://www.rca.ac.uk' + image.file.url,
            )
        else:
            return (
                "No",
                'error',
                None,
            )

    def profile_image_field(self, student):
        return self.get_image(student.profile_image)

    def postcard_image_field(self, student):
        return self.get_image(student.postcard_image)

    def carousel_items_field(self, student):
        carousel_item_count = student.get_profile()['carousel_items'].count()
        return (
            str(carousel_item_count),
            'error' if carousel_item_count == 0 else None,
            None,
        )

    title = "Catalogue check"

    fields = (
        ("Name", name_field),
        ("Page Status", page_status_field),
        ("Programme", programme_field),
        ("Email", email_field),
        ("Phone number", phone_number_field),
        ("Profile image", profile_image_field),
        ("Postcard image", postcard_image_field),
        ("Carousel items", carousel_items_field),
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

    def handle(self, year, format='csv', **options):
        students = self.students_for_year(year).order_by('phd_programme', 'mphil_programme', 'ma_programme', 'title')
        report = CatalogueCheckReport(students)

        if format == 'csv':
            with open('report.csv', 'w') as html:
                html.write(report.get_csv().encode('UTF-8'))
        elif format == 'html':
            with open('report.html', 'w') as html:
                html.write(report.get_html().encode('UTF-8'))
        else:
            print "Unrecognised output format"
