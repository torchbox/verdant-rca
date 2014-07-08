from django.core.management.base import BaseCommand
from django.db import models
from django.utils import dateformat
from django.conf import settings
from django.contrib.auth.models import User
from rca.models import NewStudentPage, RcaImage
from rca.report_generator import Report
from optparse import make_option
import dateutil.parser
from zipfile import ZipFile
from PIL import Image
import humanize
import os
import csv
import json
from itertools import chain


def get_postcard_zip_filename(student_page):
    return '-'.join([
        str(student_page.id),
        student_page.first_name.replace(' ', '-'),
        student_page.last_name.replace(' ', '-'),
    ]) + os.path.splitext(student_page.postcard_image.file.name)[1]


class StudentsReport(Report):
    def first_name_field(self, student):
        return student['first_name'], None, None

    def last_name_field(self, student):
        return student['last_name'], None, None

    def page_field(self, student):
        page = student['page']

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

    def page_status_field(self, student):
        page = student['page']

        if page:
            # Get status
            status = page.status_string.upper()

            # If page in moderation
            if page.get_latest_revision().submitted_for_moderation:
                status += " (in moderation)"

            return (
                status,
                'error' if not page.live else None,
                None,
            )
        else:
            return (
                "",
                'error',
                None,
            )

    def uploaded_images_field(self, student):
        if not student['user']:
            return (
                "User not found",
                'error',
                None,
            )

        return (
            str(len(set(student['uploaded_images']))),
            '',
            None,
        )

    def carousel_images_field(self, student):
        return (
            str(len(set(student['carousel_images']))),
            '',
            None,
        )

    def duplicate_carousel_images_field(self, student):
        return (
            str(len(student['carousel_images']) - len(set(student['carousel_images']))),
            '',
            None,
        )

    def move_images_to_field(self, student):
        page = student['page']

        if page:
            profile = page.get_profile()

            if profile:
                return (
                    profile['name'],
                    '',
                    None,
                )
            else:
                return (
                    "No school set",
                    'error',
                    None,
                )
        else:
            return (
                "",
                'error',
                None,
            )

    fields = (
        ("First Name", first_name_field),
        ("Last Name", last_name_field),
        ("Page", page_field),
        ("Page Status", page_status_field),
        ("Uploaded images", uploaded_images_field),
        ("Carousel images", carousel_images_field),
        ("Duplicate carousel images", duplicate_carousel_images_field),
        ("Move images to", move_images_to_field),
    )

    title = "Student images report"

    extra_css = """
        td.error {
            color: #DD0000;
            font-weight: bold;
        }
        td.important {
            color: #00AA00;
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

        print first_name, last_name

        # Get user for student
        user = None
        if email:
            user = User.objects.filter(email=email)

        # Get list of possible pages
        students = NewStudentPage.objects.all()

        # Find student page
        page = None

        # Find by user
        if page is None and user:
            page = students.filter(owner=user).first()

        # Find by email
        if page is None and email:
            page = students.filter(emails__email=email).first()

        # Find by name
        if page is None:
            page = students.filter(last_name__iexact=last_name, first_name__iexact=first_name).first()

        # Get latest revision
        current_revision = None
        if page:
            current_revision = page.revisions.order_by('-created_at').first()

        return {
            'first_name': first_name,
            'last_name': last_name,
            'programme': programme,
            'email': email,
            'page': page,
            'user': user,
            'current_revision': current_revision,
            'current_revision_page': current_revision.as_page_object() if current_revision else None,
            'uploaded_images': list(RcaImage.objects.filter(uploaded_by_user=user).values_list('id', flat=True)) if user else [],
            'carousel_images': list(chain(
                page.show_carousel_items.all().values_list('image_id', flat=True),
                page.mphil_carousel_items.all().values_list('image_id', flat=True),
                page.phd_carousel_items.all().values_list('image_id', flat=True),
            )) if page else [],
        }

    def handle(self, filename, **options):
        print "Generating report"
        with open(filename) as f:
            # Get list of students
            students = (self.process_student(student) for student in csv.reader(f))

            # Generate report
            report = StudentsReport(students)
            report.run()

        print "Creating zip file"
        # Create zipfile
        with ZipFile('student_images_report.zip', 'w') as zf:
            # Write report
            zf.writestr('report.html', report.get_html())
            zf.writestr('report.csv', report.get_csv())
