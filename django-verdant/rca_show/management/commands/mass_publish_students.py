import csv

from django.core.management.base import BaseCommand

from rca.models import NewStudentPage


class Command(BaseCommand):
    def find_student_page(self, student):
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

        return page

    def handle(self, filename, **options):
        with open(filename) as f:
            # Get list of students
            students = (self.find_student_page(student) for student in csv.reader(f))

            # Publish them
            for student in students:
                if not student:
                    print "CANNOT FIND PAGE"
                    continue

                # Find latest revision that is in moderation
                revision = student.revisions.filter(submitted_for_moderation=True).order_by('-created_at').first()

                if not revision:
                    print "NOT IN MODERATION:", student.id
                    continue

                # Check it's valid
                page = revision.as_page_object()
                error = False

                if not page.programme:
                    print "NOT SET PROGRAMME:", student.id
                    error = True

                if not page.school:
                    print "NOT SET SCHOOL:", student.id
                    error = True

                if not page.get_profile() or not page.get_profile()['graduation_year']:
                    print "NOT SET GRADUATION YEAR:", student.id
                    error = True

                # Skip if error found
                if error:
                    continue

                # Publish!
                revision.publish()
                print "PUBLISHED:", student.id
