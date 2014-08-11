from django.core.management.base import BaseCommand
from django.db import models
from django.utils import dateformat
from django.conf import settings
from rca.models import NewStudentPage
from rca.report_generator import Report
from optparse import make_option
import dateutil.parser
from zipfile import ZipFile
import os
import csv
import json


class StudentChangesReport(Report):
    def changed(self, student):
        if not student['current_revision']:
            return False

        return not student['previous_revision'] or student['current_revision'] != student['previous_revision']

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

    def page_change_by_field(self, student):
        if not self.changed(student) or not student['current_revision']:
            return '', None, None

        user = student['current_revision'].user
        return user.username, None, 'http://www.rca.ac.uk/admin/users/' + str(user.id) + '/'


    def page_change_at_field(self, student):
        if not self.changed(student) or not student['current_revision']:
            return '', None, None

        time = student['current_revision'].created_at
        return dateformat.format(time, 'l dS F Y P'), None, None

    def include_in_report(self, obj):
        return self.changed(obj)

    fields = (
        ("First Name", first_name_field),
        ("Last Name", last_name_field),
        ("Programme", programme_field),
        ("Email", email_field),
        ("Page", page_field),
        ("Page Status", page_status_field),
        ("Change", page_change_field),
        ("Changed by", page_change_by_field),
        ("Changed at", page_change_at_field)
    )

    def get_footer(self):
        footer = super(StudentChangesReport, self).get_footer()

        if self.kwargs['previous_date'] is not None:
            footer += "<br>Showing changes since: " + dateformat.format(self.kwargs['previous_date'], 'l dS F Y P')

        return footer

    title = "Student changes report"

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
            help='Date of previous report for reporting changes'
        ),
    )

    def process_student(self, student, previous_date=None):
        # Student info
        programme = student[0]
        first_name = student[2]
        last_name = student[1]
        email = student[3]

        print first_name, last_name

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
            revisions = page.revisions.exclude(user__username__in=['elaine.tierney', 'sarah.macdonald'])

            current_revision = revisions.order_by('-created_at').first()
            if previous_date is not None:
                previous_revision = revisions.filter(created_at__lt=previous_date).order_by('-created_at').first()
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

        with open(filename) as f:
            # Get list of students
            students = (self.process_student(student, previous_date_parsed) for student in csv.reader(f))

            # Generate report
            report = StudentChangesReport(
                students,
                previous_date=previous_date_parsed,
            )
            report.run()

        # Create zip
        with ZipFile('student_changes_report.zip', 'w') as zf:
            # Write report
            zf.writestr('report.html', report.get_html())
            zf.writestr('report.csv', report.get_csv())
