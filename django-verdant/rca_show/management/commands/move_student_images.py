import csv
import hashlib
import os
import json

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings

from wagtail.wagtailcore.models import PageRevision

from rca.models import NewStudentPage, RcaImage


class CarouselItem(object):
    def __init__(self, image):
        self.image = image
        self.pk = None


class PageRevisionProxy(PageRevision):
    class Meta:
        proxy = True

    def to_python(self):
        return json.loads(self.content_json)

    def from_python(self, python):
        self.content_json = json.dumps(python)

    def add_carousel_items(self, carousel_items, move_to_name):
        # Find move to relation name
        if move_to_name == 'ma':
            move_to_relation = 'show_carousel_items'
        elif move_to_name == 'mphil':
            move_to_relation = 'mphil_carousel_items'
        elif move_to_name == 'phd':
            move_to_relation = 'phd_carousel_items'

        # Deserialise this PageRevision
        content = json.loads(self.content_json)

        # Make sure relation is in the content
        if move_to_relation not in content:
            content[move_to_relation] = []

        # Add carousel items
        for carousel_item in carousel_items:
            content[move_to_relation].append({
                'pk': carousel_item.pk,
                'page': self.page.id,
                'image': carousel_item.image.id,
                'sort_order': 0,
                'link': '',
                'link_page': None,
                'poster_image': None,
                'embedly_url': '',
                'overlay_text': ''
            })

        # Reserialise this PageRevision
        self.content_json = json.dumps(content)

        # Save
        self.save()


class NewStudentPageProxy(NewStudentPage):
    class Meta:
        proxy = True

    def get_draft_revision(self):
        return PageRevisionProxy.objects.filter(page=self).order_by('-created_at').first()

    def get_moderation_revision(self):
        return PageRevisionProxy.objects.filter(page=self, submitted_for_moderation=True).order_by('-created_at').first()

    def get_move_to_name(self):
        profile = self.get_profile()
        if profile:
            return profile['name'].lower()

    def get_move_to_relation(self):
        move_to_name = self.get_move_to_name()

        if move_to_name == 'ma':
            return self.show_carousel_items
        elif move_to_name == 'mphil':
            return self.mphil_carousel_items
        elif move_to_name == 'phd':
            return self.phd_carousel_items

    def get_carousel_images(self):
        ma = RcaImage.objects.filter(id__in=self.show_carousel_items.exclude(image__isnull=True).values_list('image_id'))
        mphil = RcaImage.objects.filter(id__in=self.mphil_carousel_items.exclude(image__isnull=True).values_list('image_id'))
        phd = RcaImage.objects.filter(id__in=self.phd_carousel_items.exclude(image__isnull=True).values_list('image_id'))

        return ma | mphil | phd

    def add_carousel_items(self, carousel_items):
        # Add to live
        for carousel_item in carousel_items:
            db_carousel_item = self.get_move_to_relation().create(
                page=self,
                image=carousel_item.image
            )
            db_carousel_item.save()

            # Remember the PK for revisions
            carousel_item.pk = db_carousel_item.pk

        # Add to revisions
        draft_revision = self.get_draft_revision()
        if draft_revision:
            draft_revision.add_carousel_items(carousel_items, self.get_move_to_name())

        moderation_revision = self.get_moderation_revision()
        if moderation_revision:
            moderation_revision.add_carousel_items(carousel_items, self.get_move_to_name())


class RcaImageProxy(RcaImage):
    class Meta:
        proxy = True

    def get_file_hash(self):
        try:
            return hashlib.md5(open(os.path.join(settings.MEDIA_ROOT, self.file.name), 'rb').read()).hexdigest()
        except IOError:
            pass


class UserProxy(User):
    class Meta:
        proxy = True

    def get_student_page(self):
        return NewStudentPageProxy.objects.filter(owner=self).first()

    def get_uploaded_images(self):
        return RcaImageProxy.objects.filter(uploaded_by_user=self)

    def get_unique_uploaded_images(self):
        d = {
            image.get_file_hash(): image
            for image in self.get_uploaded_images()
        }

        if None in d:
            del d[None]

        return d.values()


class Command(BaseCommand):
    def get_student_user(self, student):
        # Student info
        programme = student[0]
        first_name = student[2]
        last_name = student[1]
        email = student[3]

        print first_name, last_name, ":",

        # Get user for student
        if email:
            return UserProxy.objects.filter(email=email).first()

    def handle(self, filename, **options):
        with open(filename) as f:
            # Get list of students
            for student in (self.get_student_user(student) for student in csv.reader(f)):
                # Quit if the user was not found
                if student is None:
                    print "USER NOT FOUND"
                    continue

                print student, ":",

                # Find the page and quit if this student doesn't have one
                page = student.get_student_page()
                if not page:
                    print "PAGE NOT FOUND"
                    continue

                print page.id, ":",

                # Quit if there is no where to move images to
                if page.get_move_to_name() is None:
                    print "NOWHERE TO MOVE IMAGES"
                    continue

                print page.get_move_to_name().upper(), ":",

                # Quit if the student already has carousel items
                carousel_image_count = page.get_carousel_images().count()
                print carousel_image_count, ":",
                if carousel_image_count != 0:
                    print "ALREADY HAS CAROUSEL ITEMS"
                    continue

                # Check if there are any uploaded images to move and quit if there isn't any
                images_to_move = student.get_unique_uploaded_images()
                print len(images_to_move), ":",
                if not images_to_move:
                    print "NO IMAGES TO MOVE"
                    continue

                # Get list of CarouselItem objects for those images
                carousel_items = [CarouselItem(image) for image in images_to_move]

                # Move the images
                page.add_carousel_items(carousel_items)

                print "MOVED"
