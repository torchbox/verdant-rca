from django.core.management.base import BaseCommand
from django.db import models
from rca.models import NewStudentPage
from rca.report_generator import Report
import csv


class StudentsReport(Report):
    def first_name_field(self, student):
        return student[0], None, None

    def last_name_field(self, student):
        return student[1], None, None

    def page_field(self, student):
        page = student[3]

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
        page = student[3]

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

    title = "Students report"

    fields = (
        ("First Name", first_name_field),
        ("Last Name", last_name_field),
        ("Page", page_field),
        ("Page Status", page_status_field),
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

    def process_student(self, student, year):
        # Student info
        first_name = student[1]
        last_name = student[0]
        email = student[2]

        # Get list of possible pages
        students = self.students_for_year(year)

        # Find student page
        page = None

        # Find by email
        if page is None:
            page = students.filter(emails__email=email).first()

        # Find by owner email
        if page is None:
            page = students.filter(owner__email=email).first()

        # Find by name
        if page is None:
            page = students.filter(last_name__iexact=last_name, first_name__iexact=first_name).first()

        return first_name, last_name, email, page

    def handle(self, filename, year, **options):
        # Get list of students
        students = []
        with open(filename) as f:
            for student in csv.reader(f):
                students.append(self.process_student(student, year))

        # Create report
        report = StudentsReport(students)

        # Output CSV
        with open('report.csv', 'w') as output:
            output.write(report.get_csv())

        # Output HTML
        with open('report.html', 'w') as output:
            output.write(report.get_html())
