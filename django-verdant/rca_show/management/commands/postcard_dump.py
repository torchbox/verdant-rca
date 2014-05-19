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
import humanize
import os


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

    def student_programme_field(self, student):
        profile = student.get_profile()

        if profile is not None:
            return (
                profile['programme_display'] or "Not set",
                'error' if not profile['programme_display'] else None,
                None,
            )
        else:
            return (
                "Not set",
                'error',
                None,
            )

    def student_specialism_field(self, student):
        profile = student.get_profile()
        if profile is not None and profile['name'] == "MA":
            return (
                student.ma_specialism or "Not set",
                'error' if not student.ma_specialism else None,
                None,
            )
        else:
            return (
                "Not MA student",
                None,
                None,
            )

    def get_child_objects(self, child_objects, field_name):
        if child_objects.exists():
            return (
                ' '.join([getattr(child_object, field_name) for child_object in child_objects.all()]),
                None,
                None,
            )
        else:
            return (
                "Not set",
                'error',
                None,
            )

    def student_email_field(self, student):
        return self.get_child_objects(student.emails, 'email')

    def student_phone_number_field(self, student):
        return self.get_child_objects(student.phones, 'phone')

    def student_website_field(self, student):
        return self.get_child_objects(student.websites, 'website')

    def student_carousel_items_field(self, student):
        carousel_item_count = student.get_profile()['carousel_items'].count()
        return (
            str(carousel_item_count),
            'error' if carousel_item_count == 0 else None,
            None,
        )

    def image_field(self, student):
        if student.postcard_image:
            return (
                os.path.split(student.postcard_image.file.name)[1],
                None,
                'images/' + os.path.split(student.postcard_image.file.name)[1],
            )
        else:
            return (
                "Not set",
                'error',
                None,
            )

    def file_size_field(self, student):
        if student.postcard_image:
            try:
                student.postcard_image.file.seek(0, 2)
                file_size = str(humanize.naturalsize(student.postcard_image.file.tell()))
                student.postcard_image.file.seek(0)
            except IOError:
                file_size = "Unknown"

            return (
                file_size,
                None,
                None,
            )
        else:
            return (
                "",
                'error',
                None,
            )

    def width_field(self, student):
        if student.postcard_image:
            return (
                str(student.postcard_image.width),
                None,
                None,
            )
        else:
            return (
                "",
                'error',
                None,
            )

    def height_field(self, student):
        if student.postcard_image:
            return (
                str(student.postcard_image.height),
                None,
                None,
            )
        else:
            return (
                "",
                'error',
                None,
            )

    def colour_format_field(self, student):
        if student.postcard_image:
            try:
                student.postcard_image.file.seek(0)
                image_mode = Image.open(student.postcard_image.file.file).mode
            except IOError:
                image_mode = "Unknown"

            return (
                image_mode,
                None,
                None,
            )
        else:
            return (
                "",
                'error',
                None,
            )

    def caption_field(self, student):
        if student.postcard_image:
            return (
                student.postcard_image.title,
                None,
                None,
            )
        else:
            return (
                "Not set" if student.postcard_image else "",
                'error',
                None,
            )

    def permission_field(self, student):
        if student.postcard_image and student.postcard_image.permission:
            return (
                student.postcard_image.permission,
                None,
                None,
            )
        else:
            return (
                "Not set" if student.postcard_image else "",
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
    def students_for_year(self, year):
        q = models.Q(ma_graduation_year=year) | models.Q(mphil_graduation_year=year) | models.Q(phd_graduation_year=year)
        return NewStudentPage.objects.filter(q)

    def handle(self, year, **options):
        # Get students
        students = self.students_for_year(year).order_by('phd_programme', 'mphil_programme', 'ma_programme', 'last_name', 'first_name')

        # Create zipfile
        with ZipFile('postcard_dump.zip', 'w') as zf:
            # Add postcard images into zip
            for student in students:
                if student.postcard_image:
                    filename = student.postcard_image.file.name

                    try:
                        zf.write(os.path.join(settings.MEDIA_ROOT, filename), 'images/' + os.path.split(filename)[1])
                    except (IOError, OSError) as e:
                        print e

            # Generate report
            report = PostcardDumpReport(students)
            zf.writestr('report.html', report.get_html())
            zf.writestr('report.csv', report.get_csv())
