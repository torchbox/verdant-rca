import os
import json
import hashlib
from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings

from rca.models import RcaImage


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--delete',
            action='store_true',
            dest='delete',
            default=False,
            help="Delete duplicate images"
        ),
    )

    def get_file_sha(self, filename):
        filename = os.path.join(settings.MEDIA_ROOT, filename)

        with open(filename, 'rb') as f:
            sha = hashlib.sha1(f.read()).hexdigest()

        return sha

    def sort_duplicates(self, images):
        keep = []
        delete = []

        # Delete any images that aren't being used
        for image in images:
            if image.get_usage().exists():
                keep.append(image)
            else:
                delete.append(image)

        # Make sure at least one copy of the image is kept
        if not keep:
            keep.append(delete.pop(0))

        return keep, delete

    def handle(self, delete, **options):
        sha_images = {}

        # Find images and store them in a dict by the SHA hash of their file
        for image in RcaImage.objects.all():
            sha = self.get_file_sha(image.file.name)

            if sha not in sha_images:
                sha_images[sha] = []

            sha_images[sha].append(image)

        # Remove non duplicates
        duplicate_sha_images = {
            sha: images
            for sha, images in sha_images.items()
            if len(images) > 1
        }

        deleted = []
        kept = []

        for sha, duplicate_images in duplicate_sha_images.items():
            # Work out what to delete and what to keep
            keep_images, delete_images = self.sort_duplicates(duplicate_images)

            kept.extend([
                {
                    'id': image.id,
                    'title': image.title,
                    'file': image.file.name,
                    'sha': sha,
                }
                for image in keep_images
            ])

            deleted.extend([
                {
                    'id': image.id,
                    'title': image.title,
                    'file': image.file.name,
                    'sha': sha,
                }
                for image in delete_images
            ])

            if delete:
                for image in delete_images:
                    image.delete()

        print "KEPT", json.dumps(kept)
        print "DELETED", json.dumps(deleted)
