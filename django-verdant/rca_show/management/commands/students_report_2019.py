import os
import csv
import json
from optparse import make_option
import dateutil.parser
from zipfile import ZipFile
from PIL import Image
import humanize

from django.core.management.base import BaseCommand
from django.db import models
from django.utils import dateformat
from django.conf import settings

from rca.models import NewStudentPage
from rca_show.management.report_generator import Report



def get_postcard_zip_filename(programme, student_page):
    return programme + '/' + '-'.join([
        str(student_page.id),
        student_page.first_name.replace(' ', '-'),
        student_page.last_name.replace(' ', '-'),
    ]) + os.path.splitext(student_page.postcard_image.file.name)[1]


class StudentsReport(Report):
    def changed(self, student):
        return not student['previous_revision'] or student['current_revision'] != student['previous_revision']

    def postcard_changed(self, student):
        current = None
        previous = None

        if student['current_revision']:
            revision_json = json.loads(student['current_revision'].content_json)
            if 'postcard_image' in revision_json:
                current = revision_json['postcard_image']
        else:
            return

        if student['previous_revision']:
            revision_json = json.loads(student['previous_revision'].content_json)
            if 'postcard_image' in revision_json:
                previous = revision_json['postcard_image']

        if current == previous:
            return False
        elif current != previous:
            return True

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
                'https://www.rca.ac.uk/admin/pages/' + str(page.id) + '/edit/',
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
            latest_revision = page.get_latest_revision()
            if latest_revision and latest_revision.submitted_for_moderation:
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

    def student_email_fields(self, student):
        if student['current_revision_page']:
            page = student['current_revision_page']
            for child_object in page.emails.all():
                yield (child_object.email, None, None)
        else:
            yield (
                "",
                'error',
                None,
            )


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

    def student_phone_number_fields(self, student):
        if student['current_revision_page']:
            page = student['current_revision_page']
            for child_object in page.phones.all():
                yield (child_object.phone, None, None)
        else:
            yield (
                "",
                'error',
                None,
            )

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

    def student_website_fields(self, student):
        if student['current_revision_page']:
            page = student['current_revision_page']
            for child_object in page.websites.all():
                yield (child_object.website, None, None)
        else:
            yield (
                "",
                'error',
                None,
            )

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
            filename = get_postcard_zip_filename(student['programme'], page)
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
                with open(os.path.join(settings.MEDIA_ROOT, page.postcard_image.file.name), 'rb') as f:
                    f.seek(0, 2)
                    file_size = str(humanize.naturalsize(f.tell()))
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
                image_mode = Image.open(os.path.join(settings.MEDIA_ROOT, page.postcard_image.file.name)).mode
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

    def postcard_image_photographer_field(self, student):
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
                page.postcard_image.photographer,
                None,
                None,
            )
        else:
            return (
                "Not set" if page.postcard_image else "",
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
        self.postcard_images = []

    def include_in_report(self, obj):
        force_include = False

        if self.kwargs['include_not_in'] is not None and obj['page']:
            if not self.kwargs['include_not_in'].filter(id=obj['page'].id).exists():
                force_include = True

        if not force_include:
            if self.kwargs['changed_only'] and not self.changed(obj):
                return False

            if self.kwargs['changed_postcard_only'] and not self.postcard_changed(obj):
                return False

        return True


    def post_process(self, obj, fields):
        # Add postcard image to postcard images list
        if obj['current_revision_page']:
            current = obj['current_revision_page']
            if current.postcard_image:
                filename = current.postcard_image.file.name
                self.postcard_images.append((
                    current.postcard_image.file.name,
                    get_postcard_zip_filename(obj['programme'], current),
                ))

        return fields

    @property
    def phone_number_columns(self):
        if not self.kwargs['split_columns']:
            return [("Student phone number", self.student_phone_number_field)]

        max_phone_count = NewStudentPage.objects.annotate(
            phone_count=models.Count('phones')
        ).aggregate(max=models.Max('phone_count'))['max']
        if max_phone_count == 0:
            return []
        elif max_phone_count == 1:
            return [("Student phone number", self.student_phone_number_field)]
        elif max_phone_count > 1:
            columns = []
            for i in range(0, max_phone_count):
                text = "Student phone number %s" % str(i + 1)
                columns.append((text, self.student_phone_number_fields))
            return columns

    @property
    def website_columns(self):
        if not self.kwargs['split_columns']:
            return [("Student website", self.student_website_field)]

        max_website_count = NewStudentPage.objects.annotate(
            website_count=models.Count('websites')
        ).aggregate(max=models.Max('website_count'))['max']
        if max_website_count == 0:
            return []
        elif max_website_count == 1:
            return [("Student website", self.student_website_field)]
        elif max_website_count > 1:
            columns = []
            for i in range(0, max_website_count):
                text = "Student website %s" % str(i + 1)
                columns.append((text, self.student_website_fields))
            return columns

    @property
    def email_columns(self):
        if not self.kwargs['split_columns']:
            return [("Student email", self.student_email_field)]

        max_email_count = NewStudentPage.objects.annotate(
            email_count=models.Count('emails')
        ).aggregate(max=models.Max('email_count'))['max']
        if max_email_count == 0:
            return []
        elif max_email_count == 1:
            return [("Student email", self.student_email_field)]
        elif max_email_count > 1:
            columns = []
            for i in range(0, max_email_count):
                text = "Student email %s" % str(i + 1)
                columns.append((text, self.student_email_fields))
            return columns

    @property
    def fields(self):
        fields = [
            ("First Name", self.first_name_field),
            ("Last Name", self.last_name_field),
            ("Programme", self.programme_field),
            ("Email", self.email_field),
            ("Page", self.page_field),
            ("Page Status", self.page_status_field),
            ("Student programme", self.student_programme_field),
            ("Student graduation year", self.student_graduation_year_field),
            ("Student specialism", self.student_specialism_field),
        ]

        fields += self.email_columns
        fields += self.phone_number_columns
        fields += self.website_columns

        fields += [
            ("Student carousel items", self.student_carousel_items_field),
            ("Change", self.page_change_field),
        ]

        if not self.kwargs['without_images']:
            fields += [("Postcard image", self.postcard_image_field)]

        fields += [
            ("Postcard change", self.postcard_image_change_field),
            ("Postcard file size", self.postcard_image_file_size_field),
            ("Postcard width", self.postcard_image_width_field),
            ("Postcard height", self.postcard_image_height_field),
            ("Postcard colour format", self.postcard_image_colour_format_field),
            ("Postcard caption", self.postcard_image_caption_field),
            ("Postcard photographer", self.postcard_image_photographer_field),
            ("Postcard permission", self.postcard_image_permission_field),
        ]

        return fields

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
        make_option('--split-columns',
            action='store_true',
            dest='split_columns',
            default=False,
            help='if --split-columns is set, phone numbers, email addresses and websites will be printed in separate columns'),
        make_option('--without-images',
            action='store_true',
            dest='without_images',
            default=False,
            help='if --without-images is set, this will exclude postcard images from a report archive.'),
    )

    def process_student(self, student, previous_date=None):
        # Student info
        programme = student[0]
        first_name = student[1]
        last_name = student[2]
        email = student[5]
        page = None

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

        print "Generating report"
        with open(filename) as f:
            # Get list of students
            students = (self.process_student(student, previous_date_parsed) for student in csv.reader(f))

            # Generate report
            report = StudentsReport(
                students,
                previous_date=previous_date_parsed,
                changed_only=options['changed_only'],
                changed_postcard_only=options['changed_postcard_only'],
                include_not_in=include_not_in,
                split_columns=options['split_columns'],
                without_images=options['without_images']
            )
            report.run()

        print "Creating zip file"
        # Create zipfile
        with ZipFile('students_report.zip', 'w') as zf:
            # Add postcard images into zip
            if not options['without_images']:
                for postcard_image in report.postcard_images:
                    try:
                        zf.write(os.path.join(settings.MEDIA_ROOT, postcard_image[0]), 'images/' + postcard_image[1])
                    except (IOError, OSError) as e:
                        print e

            # Write report
            zf.writestr('report.html', report.get_html())
            zf.writestr('report.csv', report.get_csv())
