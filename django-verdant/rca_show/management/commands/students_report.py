from django.core.management.base import BaseCommand
from django.db import models
from django.utils import dateformat
from django.conf import settings
from rca.models import NewStudentPage
from rca.report_generator import Report
from optparse import make_option
import dateutil.parser
from zipfile import ZipFile
import humanize
import os
import csv
import json


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

    def programme_field(self, student):
        return student['programme'], None, None

    def email_field(self, student):
        return student['email'], None, None

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

    def page_change_field(self, student):
        if student['current_revision']:
            if student['previous_revision']:
                if student['current_revision'] != student['previous_revision']:
                    return (
                        "Changed",
                        'changed',
                        None,
                    )
                else:
                    return (
                        "Not changed",
                        None,
                        None,
                    )
            else:
                return (
                    "Created",
                    'important',
                    None,
                )
        else:
            return (
                "",
                'error',
                None,
            )

    def postcard_image_field(self, student):
        if student['current_revision']:
            revision_json = json.loads(student['current_revision'].content_json)
            if 'postcard_image' in revision_json and revision_json['postcard_image']:
                return (
                    "Yes",
                    None,
                    None,
                )
            else:
                return (
                    "No",
                    'error',
                    None,
                )
        else:
            return (
                "",
                'error',
                None,
            )

    def postcard_image_change_field(self, student):
        current = None
        previous = None

        if student['current_revision']:
            revision_json = json.loads(student['current_revision'].content_json)
            if 'postcard_image' in revision_json:
                current = revision_json['postcard_image']
        else:
            return (
                "",
                'error',
                None,
            )

        if student['previous_revision']:
            revision_json = json.loads(student['previous_revision'].content_json)
            if 'postcard_image' in revision_json:
                previous = revision_json['postcard_image']

        if current == previous:
            return (
                "Not changed",
                None,
                None,
            )
        elif current and not previous:
            return (
                "Added",
                'important',
                None,
            )
        elif previous and not current:
            return (
                "Removed",
                'error',
                None,
            )
        elif current != previous:
            return (
                "Changed",
                'changed',
                None,
            )

    def student_programme_field(self, student):
        if student['current_revision_page']:
            page = student['current_revision_page']
        else:
            return (
                "",
                'error',
                None,
            )

        profile = page.get_profile()

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

    def student_graduation_year_field(self, student):
        page = student['page']

        if page:
            profile = page.get_profile()

            if profile:
                if profile['graduation_year']:
                    return (
                        profile['graduation_year'],
                        None,
                        None,
                    )
                else:
                    return (
                        "Not set",
                        'error',
                        None,
                    )
        return (
            "",
            'error',
            None,
        )

    def student_specialism_field(self, student):
        if student['current_revision_page']:
            page = student['current_revision_page']
        else:
            return (
                "",
                'error',
                None,
            )

        profile = page.get_profile()
        if profile is not None and profile['name'] == "MA":
            return (
                page.ma_specialism or "Not set",
                'error' if not page.ma_specialism else None,
                None,
            )
        else:
            return (
                "Not MA student",
                None,
                None,
            )

    def get_child_objects(self, child_objects, field_name):
        if child_objects.count() > 0:
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
        if student['current_revision_page']:
            page = student['current_revision_page']
        else:
            return (
                "",
                'error',
                None,
            )

        return self.get_child_objects(page.emails, 'email')

    def student_phone_number_field(self, student):
        if student['current_revision_page']:
            page = student['current_revision_page']
        else:
            return (
                "",
                'error',
                None,
            )

        return self.get_child_objects(page.phones, 'phone')

    def student_website_field(self, student):
        if student['current_revision_page']:
            page = student['current_revision_page']
        else:
            return (
                "",
                'error',
                None,
            )

        return self.get_child_objects(page.websites, 'website')

    def student_carousel_items_field(self, student):
        if student['current_revision_page']:
            page = student['current_revision_page']
        else:
            return (
                "",
                'error',
                None,
            )

        profile = page.get_profile()

        if profile is not None:
            carousel_item_count = profile['carousel_items'].count()
            return (
                str(carousel_item_count),
                'error' if carousel_item_count == 0 else None,
                None,
            )
        else:
            return (
                '0',
                'error',
                None,
            )

    def postcard_image_field(self, student):
        if student['current_revision_page']:
            page = student['current_revision_page']
        else:
            return (
                "",
                'error',
                None,
            )

        if page.postcard_image:
            filename = get_postcard_zip_filename(page)
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

    def postcard_image_file_size_field(self, student):
        if student['current_revision_page']:
            page = student['current_revision_page']
        else:
            return (
                "",
                'error',
                None,
            )

        if page.postcard_image:
            try:
                page.postcard_image.file.seek(0, 2)
                file_size = str(humanize.naturalsize(page.postcard_image.file.tell()))
                page.postcard_image.file.seek(0)
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

    def postcard_image_width_field(self, student):
        if student['current_revision_page']:
            page = student['current_revision_page']
        else:
            return (
                "",
                'error',
                None,
            )

        if page.postcard_image:
            return (
                str(page.postcard_image.width),
                None,
                None,
            )
        else:
            return (
                "",
                'error',
                None,
            )

    def postcard_image_height_field(self, student):
        if student['current_revision_page']:
            page = student['current_revision_page']
        else:
            return (
                "",
                'error',
                None,
            )

        if page.postcard_image:
            return (
                str(page.postcard_image.height),
                None,
                None,
            )
        else:
            return (
                "",
                'error',
                None,
            )

    def postcard_image_colour_format_field(self, student):
        if student['current_revision_page']:
            page = student['current_revision_page']
        else:
            return (
                "",
                'error',
                None,
            )

        if page.postcard_image:
            try:
                page.postcard_image.file.seek(0)
                image_mode = Image.open(page.postcard_image.file.file).mode
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

    def postcard_image_caption_field(self, student):
        if student['current_revision_page']:
            page = student['current_revision_page']
        else:
            return (
                "",
                'error',
                None,
            )

        if page.postcard_image:
            return (
                page.postcard_image.title,
                None,
                None,
            )
        else:
            return (
                "Not set" if page.postcard_image else "",
                'error',
                None,
            )

    def postcard_image_permission_field(self, student):
        if student['current_revision_page']:
            page = student['current_revision_page']
        else:
            return (
                "",
                'error',
                None,
            )

        if page.postcard_image and page.postcard_image.permission:
            return (
                page.postcard_image.permission,
                None,
                None,
            )
        else:
            return (
                "Not set" if page.postcard_image else "",
                'error',
                None,
            )

    def __init__(self, *args, **kwargs):
        super(StudentsReport, self).__init__(*args, **kwargs)
        self.included_students = []

    def post_process(self, obj, fields):
        force_include = False

        if self.kwargs['include_not_in'] is not None and obj['page']:
            if not self.kwargs['include_not_in'].filter(id=obj['page'].id).exists():
                force_include = True

        if not force_include:
            if self.kwargs['changed_only'] and fields[13][0] == "Not changed":
                return

            if self.kwargs['changed_postcard_only'] and fields[15][0] == "Not changed":
                return

        self.included_students.append(obj)

        return fields

    fields = (
        ("First Name", first_name_field),
        ("Last Name", last_name_field),
        ("Programme", programme_field),
        ("Email", email_field),
        ("Page", page_field),
        ("Page Status", page_status_field),
        ("Student programme", student_programme_field),
        ("Student graduation year", student_graduation_year_field),
        ("Student specialism", student_specialism_field),
        ("Student email", student_email_field),
        ("Student phone number", student_phone_number_field),
        ("Student website", student_website_field),
        ("Student carousel items", student_carousel_items_field),
        ("Change", page_change_field),
        ("Postcard image", postcard_image_field),
        ("Postcard change", postcard_image_change_field),
        ("Postcard file size", postcard_image_file_size_field),
        ("Postcard width", postcard_image_width_field),
        ("Postcard height", postcard_image_height_field),
        ("Postcard colour format", postcard_image_colour_format_field),
        ("Postcard caption", postcard_image_caption_field),
        ("Postcard permission", postcard_image_permission_field),
    )

    def get_footer(self):
        footer = super(StudentsReport, self).get_footer()

        if self.kwargs['previous_date'] is not None:
            footer += "<br>Showing changes since: " + dateformat.format(self.kwargs['previous_date'], 'l dS F Y P')

        return footer

    title = "Students report"

    extra_css = """
        td.error {
            color: #DD0000;
            font-weight: bold;
        }
        td.important {
            color: #00AA00;
            font-weight: bold;
        }
        td.changed {
            color: #DDAA00;
            font-weight: bold;
        }
        """


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--changes-since',
            action='store',
            type='string',
            dest='previous_date',
            default=None,
            help='Date of previous report for reporting changes'),
        make_option('--changed-only',
            action='store_true',
            dest='changed_only',
            default=False,
            help='If --changes-since is used. This will exclude any students that haven\'t changed'),
        make_option('--changed-postcard-only',
            action='store_true',
            dest='changed_postcard_only',
            default=False,
            help='If --changes-since is used. This will exclude any students that haven\'t changed their postcard'),
        make_option('--include-not-in',
            action='store',
            type='string',
            dest='include_not_in',
            default=None,
            help='If changed-only is set. Any students not in the list in this file will be included in the report'),
        )

    def process_student(self, student, previous_date=None):
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

        # Get revisions
        current_revision = None
        previous_revision = None
        if page:
            current_revision = page.revisions.order_by('-created_at').first()
            if previous_date is not None:
                previous_revision = page.revisions.filter(created_at__lt=previous_date).order_by('-created_at').first()
            else:
                previous_revision = current_revision

        return {
            'first_name': first_name,
            'last_name': last_name,
            'programme': programme,
            'email': email,
            'page': page,
            'current_revision': current_revision,
            'previous_revision': previous_revision,
            'current_revision_page': current_revision.as_page_object() if current_revision else None,
        }

    def handle(self, filename, **options):
        # Parse date
        previous_date_parsed = None
        if options['previous_date']:
            previous_date_parsed = dateutil.parser.parse(options['previous_date'])

        # Get include_not_in
        include_not_in = None
        if options['include_not_in']:
            with open(options['include_not_in']) as f:
                include_not_in = NewStudentPage.objects.filter(pk__in=list(f))

        # Get list of students
        students = []
        with open(filename) as f:
            for student in csv.reader(f):
                students.append(self.process_student(student, previous_date_parsed))

        # Generate report
        report = StudentsReport(
            students,
            previous_date=previous_date_parsed,
            changed_only=options['changed_only'],
            changed_postcard_only=options['changed_postcard_only'],
            include_not_in=include_not_in,
        )
        report.run()

        # Create zipfile
        with ZipFile('students_report.zip', 'w') as zf:
            # Add postcard images into zip
            for student in report.included_students:
                if student['current_revision_page']:
                    current = student['current_revision_page']
                    if current.postcard_image:
                        filename = current.postcard_image.file.name

                        try:
                            zf.write(os.path.join(settings.MEDIA_ROOT, filename), 'images/' + get_postcard_zip_filename(current))
                        except (IOError, OSError) as e:
                            print e

            # Write report
            zf.writestr('report.html', report.get_html())
            zf.writestr('report.csv', report.get_csv())
