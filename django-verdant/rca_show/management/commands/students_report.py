from django.core.management.base import BaseCommand
from django.db import models
from django.utils import dateformat
from rca.models import NewStudentPage
from rca.report_generator import Report
from optparse import make_option
import dateutil.parser
import csv
import json


class StudentsReport(Report):
    def first_name_field(self, student):
        return student['first_name'], None, None

    def last_name_field(self, student):
        return student['last_name'], None, None

    def email_field(self, student):
        return student['email'], None, None

    def programme_field(self, student):
        return student['programme'], None, None

    def graduation_year_field(self, student):
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
        page = student['page']

        if page:
            if page.postcard_image:
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

    def post_process(self, fields):
        if self.kwargs['changed_only'] and fields[6][0] == "Not changed":
            return
        return fields

    fields = (
        ("First Name", first_name_field),
        ("Last Name", last_name_field),
        ("Email", email_field),
        ("Programme", programme_field),
        ("Graduation year", graduation_year_field),
        ("Page", page_field),
        ("Page Status", page_status_field),
        ("Change", page_change_field),
        ("Has postcard", postcard_image_field),
        ("Postcard change", postcard_image_change_field),
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
        }

    def handle(self, filename, **options):
        # Parse date
        previous_date_parsed = None
        if options['previous_date']:
            previous_date_parsed = dateutil.parser.parse(options['previous_date'])

        # Get list of students
        students = []
        with open(filename) as f:
            for student in csv.reader(f):
                students.append(self.process_student(student, previous_date_parsed))

        print students

        # Create report
        report = StudentsReport(students, previous_date=previous_date_parsed, changed_only=options['changed_only'])

        # Output CSV
        with open('report.csv', 'w') as output:
            output.write(report.get_csv())

        # Output HTML
        with open('report.html', 'w') as output:
            output.write(report.get_html())
