from django.test import TestCase
from .models import Band, BandMember
from cluster.forms import transientmodelformset_factory, childformset_factory


class ClusterTest(TestCase):
    def test_can_create_cluster(self):
        beatles = Band(name='The Beatles')

        self.assertEqual(0, beatles.members.count())

        beatles.members = [
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ]
        self.assertEqual(2, beatles.members.count())

        # these should not exist in the database yet
        self.assertFalse(Band.objects.filter(name='The Beatles').exists())
        self.assertFalse(BandMember.objects.filter(name='John Lennon').exists())

        beatles.save()
        # this should create database entries
        self.assertTrue(Band.objects.filter(name='The Beatles').exists())
        self.assertTrue(BandMember.objects.filter(name='John Lennon').exists())

    def test_can_pass_child_relations_as_constructor_kwargs(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])
        self.assertEqual(2, beatles.members.count())

class TransientFormsetTest(TestCase):
    BandMembersFormset = transientmodelformset_factory(BandMember, exclude=['band'], extra=3)

    def test_can_create_formset(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])
        band_members_formset = self.BandMembersFormset(queryset=beatles.members.all())

        self.assertEqual(5, len(band_members_formset.forms))
        self.assertEqual('John Lennon', band_members_formset.forms[0].instance.name)

    def test_incoming_formset_data(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='George Harrison'),
        ])

        band_members_formset = self.BandMembersFormset({
            'form-TOTAL_FORMS': 3,
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': 1000,

            'form-0-name': 'John Lennon',
            'form-0-id': '',

            'form-1-name': 'Paul McCartney',
            'form-1-id': '',

            'form-2-name': '',
            'form-2-id': '',
        }, queryset=beatles.members.all())

        self.assertTrue(band_members_formset.is_valid())
        members = band_members_formset.save(commit=False)
        self.assertEqual(2, len(members))
        self.assertEqual('John Lennon', members[0].name)
        # should not exist in the database yet
        self.assertFalse(BandMember.objects.filter(name='John Lennon').exists())

class ChildFormsetTest(TestCase):
    def test_can_create_formset(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])
        BandMembersFormset = childformset_factory(Band, BandMember, extra=3)
        band_members_formset = BandMembersFormset(instance=beatles)

        self.assertEqual(5, len(band_members_formset.forms))
        self.assertEqual('John Lennon', band_members_formset.forms[0].instance.name)

    def test_incoming_formset_data(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='George Harrison'),
        ])
        BandMembersFormset = childformset_factory(Band, BandMember, extra=3)

        band_members_formset = BandMembersFormset({
            'form-TOTAL_FORMS': 4,
            'form-INITIAL_FORMS': 1,
            'form-MAX_NUM_FORMS': 1000,

            'form-0-name': 'George Harrison',
            'form-0-DELETE': 'form-0-DELETE',
            'form-0-id': '',

            'form-1-name': 'John Lennon',
            'form-1-id': '',

            'form-2-name': 'Paul McCartney',
            'form-2-id': '',

            'form-3-name': '',
            'form-3-id': '',
        }, instance=beatles)

        self.assertTrue(band_members_formset.is_valid())
        members = band_members_formset.save(commit=False)

        self.assertEqual(2, len(members))
        self.assertEqual('John Lennon', members[0].name)

        self.assertEqual(2, beatles.members.count())
        self.assertEqual('John Lennon', beatles.members.all()[0].name)

        # should not exist in the database yet
        self.assertFalse(BandMember.objects.filter(name='John Lennon').exists())

        beatles.save()
        # this should create database entries
        self.assertTrue(Band.objects.filter(name='The Beatles').exists())
        self.assertTrue(BandMember.objects.filter(name='John Lennon').exists())
