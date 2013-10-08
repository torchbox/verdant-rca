from django.test import TestCase
from .models import Band, BandMember


class ClusterTest(TestCase):
    def test_can_create_cluster(self):
        beatles = Band(name='The Beatles')

        self.assertFalse(beatles.members.all())

        beatles.members = [
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ]
        self.assertTrue(beatles.members.all())
