"""
This command checks through all student images
ie the images used for their show page,
and counts the filesize.

Suggested use is to sync local db with production
and run this locally but with exported production AWS (S3) credentials.
"""
from django.core.management.base import BaseCommand
from rca.models import NewStudentPage
from optparse import make_option


class Command(BaseCommand):
    def __init__(self):
        self.total_student_image_size = 0
        self.num_student_images = 0
        self.errors = 0
        self.quit_on_error = False

    option_list = BaseCommand.option_list + (
            make_option('--limit',
                action='store',
                type='int',
                dest='limit',
                default=None,
                help='Limit to number of students processed'
            ),
            make_option(
                '--quit-on-error',
                action='store_true',
                dest='quit_on_error',
                default=False,
                help="Quit if file size cannot be read.",
            ),
        )

    def add_image_to_total(self, image):
        try:
            self.num_student_images += 1
            self.total_student_image_size += image.get_file_size()
        except Exception:
            self.errors += 1
            if self.quit_on_error:
                print("Encountered error getting file size for image id:{}".format(image.id))
                quit()

    def handle(self, **options):
        # Get students
        if options['limit']:
            limit = options['limit']
            students = NewStudentPage.objects.all().order_by('-id')[:limit]
        else:
            students = NewStudentPage.objects.all()

        self.quit_on_error = options['quit_on_error']

        for students_processed, student in enumerate(students, start=1):
            if student.postcard_image:
                self.add_image_to_total(student.postcard_image)

            carousel_items = student.show_carousel_items.all()
            if carousel_items:
                for item in carousel_items:
                    if item.image:
                        self.add_image_to_total(item.image)
                    if item.poster_image:
                        self.add_image_to_total(item.poster_image)
            print(students_processed)

        print("Errors getting file size:")
        print(self.errors)
        print("Number of student images:")
        print(self.num_student_images)
        print("Total filesize:")

        from django.template.defaultfilters import filesizeformat
        print(filesizeformat(self.total_student_image_size))
