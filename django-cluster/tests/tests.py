from django.test import TestCase
from .models import Band, BandMember, Album, Restaurant
from cluster.forms import transientmodelformset_factory, childformset_factory, ClusterForm
from django.forms import Textarea, CharField
from django.db import IntegrityError

import datetime


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

        john_lennon = BandMember.objects.get(name='John Lennon')
        beatles.members = [john_lennon]
        # reassigning should take effect on the in-memory record
        self.assertEqual(1, beatles.members.count())
        # but not the database
        self.assertEqual(2, Band.objects.get(name='The Beatles').members.count())

        beatles.save()
        # now updated in the database
        self.assertEqual(1, Band.objects.get(name='The Beatles').members.count())
        self.assertEqual(1, BandMember.objects.filter(name='John Lennon').count())
        # removed member should be deleted from the db entirely
        self.assertEqual(0, BandMember.objects.filter(name='Paul McCartney').count())

        # queries on beatles.members should now revert to SQL
        self.assertTrue(beatles.members.extra(where=["tests_bandmember.name='John Lennon'"]).exists())

    def test_related_manager_assignment_ops(self):
        beatles = Band(name='The Beatles')
        john = BandMember(name='John Lennon')
        paul = BandMember(name='Paul McCartney')

        beatles.members.add(john)
        self.assertEqual(1, beatles.members.count())

        beatles.members.add(paul)
        self.assertEqual(2, beatles.members.count())
        # ensure that duplicates are filtered
        beatles.members.add(paul)
        self.assertEqual(2, beatles.members.count())

        beatles.members.remove(john)
        self.assertEqual(1, beatles.members.count())
        self.assertEqual(paul, beatles.members.all()[0])

        george = beatles.members.create(name='George Harrison')
        self.assertEqual(2, beatles.members.count())
        self.assertEqual('George Harrison', george.name)

    def test_can_pass_child_relations_as_constructor_kwargs(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])
        self.assertEqual(2, beatles.members.count())
        self.assertEqual(beatles, beatles.members.all()[0].band)

    def test_can_only_commit_on_saved_parent(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])
        self.assertRaises(IntegrityError, lambda: beatles.members.commit())

        beatles.save()
        beatles.members.commit()

class TransientFormsetTest(TestCase):
    BandMembersFormset = transientmodelformset_factory(BandMember, exclude=['band'], extra=3, can_delete=True)

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

    def test_save_commit_false(self):
        john = BandMember(name='John Lennon')
        paul = BandMember(name='Paul McCartney')
        ringo = BandMember(name='Richard Starkey')
        beatles = Band(name='The Beatles', members=[
            john, paul, ringo
        ])
        beatles.save()

        john_id, paul_id, ringo_id = john.id, paul.id, ringo.id

        self.assertTrue(john_id)
        self.assertTrue(paul_id)

        band_members_formset = self.BandMembersFormset({
            'form-TOTAL_FORMS': 5,
            'form-INITIAL_FORMS': 3,
            'form-MAX_NUM_FORMS': 1000,

            'form-0-name': 'John Lennon',
            'form-0-DELETE': 'form-0-DELETE',
            'form-0-id': john_id,

            'form-1-name': 'Paul McCartney',
            'form-1-id': paul_id,

            'form-2-name': 'Ringo Starr',  # changing data of an existing record
            'form-2-id': ringo_id,

            'form-3-name': '',
            'form-3-id': '',

            'form-4-name': 'George Harrison',  # Adding a record
            'form-4-id': '',
        }, queryset=beatles.members.all())
        self.assertTrue(band_members_formset.is_valid())

        updated_members = band_members_formset.save(commit=False)
        self.assertEqual(2, len(updated_members))
        self.assertEqual('Ringo Starr', updated_members[0].name)
        self.assertEqual(ringo_id, updated_members[0].id)

        # should not be updated in the db yet
        self.assertEqual('Richard Starkey', BandMember.objects.get(id=ringo_id).name)

        self.assertEqual('George Harrison', updated_members[1].name)
        self.assertFalse(updated_members[1].id)  # no ID yet

    def test_save_commit_true(self):
        john = BandMember(name='John Lennon')
        paul = BandMember(name='Paul McCartney')
        ringo = BandMember(name='Richard Starkey')
        beatles = Band(name='The Beatles', members=[
            john, paul, ringo
        ])
        beatles.save()

        john_id, paul_id, ringo_id = john.id, paul.id, ringo.id

        self.assertTrue(john_id)
        self.assertTrue(paul_id)

        band_members_formset = self.BandMembersFormset({
            'form-TOTAL_FORMS': 4,
            'form-INITIAL_FORMS': 3,
            'form-MAX_NUM_FORMS': 1000,

            'form-0-name': 'John Lennon',
            'form-0-DELETE': 'form-0-DELETE',
            'form-0-id': john_id,

            'form-1-name': 'Paul McCartney',
            'form-1-id': paul_id,

            'form-2-name': 'Ringo Starr',  # changing data of an existing record
            'form-2-id': ringo_id,

            'form-3-name': '',
            'form-3-id': '',
        }, queryset=beatles.members.all())
        self.assertTrue(band_members_formset.is_valid())

        updated_members = band_members_formset.save()
        self.assertEqual(1, len(updated_members))
        self.assertEqual('Ringo Starr', updated_members[0].name)
        self.assertEqual(ringo_id, updated_members[0].id)

        self.assertFalse(BandMember.objects.filter(id=john_id).exists())
        self.assertEqual('Paul McCartney', BandMember.objects.get(id=paul_id).name)
        self.assertEqual(beatles.id, BandMember.objects.get(id=paul_id).band_id)
        self.assertEqual('Ringo Starr', BandMember.objects.get(id=ringo_id).name)
        self.assertEqual(beatles.id, BandMember.objects.get(id=ringo_id).band_id)


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

    def test_empty_formset(self):
        BandMembersFormset = childformset_factory(Band, BandMember, extra=3)
        band_members_formset = BandMembersFormset()
        self.assertEqual(3, len(band_members_formset.forms))

    def test_save_commit_false(self):
        john = BandMember(name='John Lennon')
        paul = BandMember(name='Paul McCartney')
        ringo = BandMember(name='Richard Starkey')
        beatles = Band(name='The Beatles', members=[
            john, paul, ringo
        ])
        beatles.save()
        john_id, paul_id, ringo_id = john.id, paul.id, ringo.id

        BandMembersFormset = childformset_factory(Band, BandMember, extra=3)

        band_members_formset = BandMembersFormset({
            'form-TOTAL_FORMS': 5,
            'form-INITIAL_FORMS': 3,
            'form-MAX_NUM_FORMS': 1000,

            'form-0-name': 'John Lennon',
            'form-0-DELETE': 'form-0-DELETE',
            'form-0-id': john_id,

            'form-1-name': 'Paul McCartney',
            'form-1-id': paul_id,

            'form-2-name': 'Ringo Starr',  # changing data of an existing record
            'form-2-id': ringo_id,

            'form-3-name': '',
            'form-3-id': '',

            'form-4-name': 'George Harrison',  # adding a record
            'form-4-id': '',
        }, instance=beatles)
        self.assertTrue(band_members_formset.is_valid())
        updated_members = band_members_formset.save(commit=False)

        # updated_members should only include the items that have been changed and not deleted
        self.assertEqual(2, len(updated_members))
        self.assertEqual('Ringo Starr', updated_members[0].name)
        self.assertEqual(ringo_id, updated_members[0].id)

        self.assertEqual('George Harrison', updated_members[1].name)
        self.assertEqual(None, updated_members[1].id)

        # Changes should not be committed to the db yet
        self.assertTrue(BandMember.objects.filter(name='John Lennon', id=john_id).exists())
        self.assertEqual('Richard Starkey', BandMember.objects.get(id=ringo_id).name)
        self.assertFalse(BandMember.objects.filter(name='George Harrison').exists())

        beatles.members.commit()
        # this should create/update/delete database entries
        self.assertEqual('Ringo Starr', BandMember.objects.get(id=ringo_id).name)
        self.assertTrue(BandMember.objects.filter(name='George Harrison').exists())
        self.assertFalse(BandMember.objects.filter(name='John Lennon').exists())

class SerializeTest(TestCase):
    def test_serialize(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])

        expected = {'pk': None, 'albums': [], 'name': u'The Beatles', 'members': [{'pk': None, 'name': u'John Lennon', 'band': None}, {'pk': None, 'name': u'Paul McCartney', 'band': None}]}
        self.assertEqual(expected, beatles.serializable_data())

    def test_serialize_json_with_dates(self):
        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ], albums=[
            Album(name='Rubber Soul', release_date=datetime.date(1965, 12, 3))
        ])

        beatles_json = beatles.to_json()
        self.assertTrue("John Lennon" in beatles_json)
        self.assertTrue("1965-12-03" in beatles_json)
        unpacked_beatles = Band.from_json(beatles_json)
        self.assertEqual(datetime.date(1965, 12, 3), unpacked_beatles.albums.all()[0].release_date)

    def test_deserialize(self):
        beatles = Band.from_serializable_data({
            'pk': 9,
            'albums': [],
            'name': u'The Beatles',
            'members': [
                {'pk': None, 'name': u'John Lennon', 'band': None},
                {'pk': None, 'name': u'Paul McCartney', 'band': None},
            ]
        })
        self.assertEqual(9, beatles.id)
        self.assertEqual('The Beatles', beatles.name)
        self.assertEqual(2, beatles.members.count())
        self.assertEqual(BandMember, beatles.members.all()[0].__class__)

    def test_deserialize_json(self):
        beatles = Band.from_json('{"pk": 9, "albums": [], "name": "The Beatles", "members": [{"pk": null, "name": "John Lennon", "band": null}, {"pk": null, "name": "Paul McCartney", "band": null}]}')
        self.assertEqual(9, beatles.id)
        self.assertEqual('The Beatles', beatles.name)
        self.assertEqual(2, beatles.members.count())
        self.assertEqual(BandMember, beatles.members.all()[0].__class__)

    def test_deserialize_with_multi_table_inheritance(self):
        fatduck = Restaurant.from_json('{"pk": 42, "name": "The Fat Duck", "serves_hot_dogs": false}')
        self.assertEqual(42, fatduck.id)

        data = fatduck.serializable_data()
        self.assertEqual(42, data['pk'])
        self.assertEqual("The Fat Duck", data['name'])

class ClusterFormTest(TestCase):
    def test_cluster_form(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band

        self.assertTrue(BandForm.formsets)

        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])

        form = BandForm(instance=beatles)

        self.assertEqual(5, len(form.formsets['members'].forms))

    def test_empty_cluster_form(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band

        form = BandForm()
        self.assertEqual(3, len(form.formsets['members'].forms))

    def test_incoming_form_data(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band

        beatles = Band(name='The Beatles', members=[
            BandMember(name='George Harrison'),
        ])
        form = BandForm({
            'name': "The Beatles",

            'members-TOTAL_FORMS': 4,
            'members-INITIAL_FORMS': 1,
            'members-MAX_NUM_FORMS': 1000,

            'members-0-name': 'George Harrison',
            'members-0-DELETE': 'members-0-DELETE',
            'members-0-id': '',

            'members-1-name': 'John Lennon',
            'members-1-id': '',

            'members-2-name': 'Paul McCartney',
            'members-2-id': '',

            'members-3-name': '',
            'members-3-id': '',

            'albums-TOTAL_FORMS': 0,
            'albums-INITIAL_FORMS': 0,
            'albums-MAX_NUM_FORMS': 1000,
        }, instance=beatles)

        self.assertTrue(form.is_valid())
        result = form.save(commit=False)
        self.assertEqual(result, beatles)

        self.assertEqual(2, beatles.members.count())
        self.assertEqual('John Lennon', beatles.members.all()[0].name)

        # should not exist in the database yet
        self.assertFalse(BandMember.objects.filter(name='John Lennon').exists())

        beatles.save()
        # this should create database entries
        self.assertTrue(Band.objects.filter(name='The Beatles').exists())
        self.assertTrue(BandMember.objects.filter(name='John Lennon').exists())

    def test_widget_overrides(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band
                widgets = {
                    'name': Textarea(),
                    'members': {
                        'name': Textarea()
                    }
                }

        form = BandForm()
        self.assertEqual(Textarea, type(form['name'].field.widget))
        self.assertEqual(Textarea, type(form.formsets['members'].forms[0]['name'].field.widget))

    def test_formfield_callback(self):

        def formfield_for_dbfield(db_field, **kwargs):
            # a particularly stupid formfield_callback that just uses Textarea for everything
            return CharField(widget=Textarea, **kwargs)

        class BandFormWithFFC(ClusterForm):
            formfield_callback = formfield_for_dbfield
            class Meta:
                model = Band

        form = BandFormWithFFC()
        self.assertEqual(Textarea, type(form['name'].field.widget))
        self.assertEqual(Textarea, type(form.formsets['members'].forms[0]['name'].field.widget))

    def test_saved_items(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band

        beatles = Band(name='The Beatles', members=[
            BandMember(name='John Lennon'),
            BandMember(name='Paul McCartney'),
        ])
        beatles.save()
        member0, member1 = beatles.members.all()
        self.assertTrue(member0.id)
        self.assertTrue(member1.id)

        form = BandForm({
            'name': "The New Beatles",

            'members-TOTAL_FORMS': 4,
            'members-INITIAL_FORMS': 2,
            'members-MAX_NUM_FORMS': 1000,

            'members-0-name': member0.name,
            'members-0-DELETE': 'members-0-DELETE',
            'members-0-id': member0.id,

            'members-1-name': member1.name,
            'members-1-id': member1.id,

            'members-2-name': 'George Harrison',
            'members-2-id': '',

            'members-3-name': '',
            'members-3-id': '',

            'albums-TOTAL_FORMS': 0,
            'albums-INITIAL_FORMS': 0,
            'albums-MAX_NUM_FORMS': 1000,
        }, instance=beatles)
        self.assertTrue(form.is_valid())
        form.save()

        new_beatles = Band.objects.get(id=beatles.id)
        self.assertEqual('The New Beatles', new_beatles.name)
        self.assertTrue(BandMember.objects.filter(name='George Harrison').exists())
        self.assertFalse(BandMember.objects.filter(name='John Lennon').exists())

    def test_creation(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band

        form = BandForm({
            'name': "The Beatles",

            'members-TOTAL_FORMS': 4,
            'members-INITIAL_FORMS': 0,
            'members-MAX_NUM_FORMS': 1000,

            'members-0-name': 'John Lennon',
            'members-0-id': '',

            'members-1-name': 'Paul McCartney',
            'members-1-id': '',

            'members-2-name': 'Pete Best',
            'members-2-DELETE': 'members-0-DELETE',
            'members-2-id': '',

            'members-3-name': '',
            'members-3-id': '',

            'albums-TOTAL_FORMS': 0,
            'albums-INITIAL_FORMS': 0,
            'albums-MAX_NUM_FORMS': 1000,
        })
        self.assertTrue(form.is_valid())
        beatles = form.save()

        self.assertTrue(beatles.id)
        self.assertEqual('The Beatles', beatles.name)
        self.assertEqual('The Beatles', Band.objects.get(id=beatles.id).name)
        self.assertEqual(2, beatles.members.count())
        self.assertTrue(BandMember.objects.filter(name='John Lennon').exists())
        self.assertFalse(BandMember.objects.filter(name='Pete Best').exists())

    def test_sort_order_is_output_on_form(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band

        form = BandForm()
        form_html = form.as_p()
        self.assertTrue('albums-0-ORDER' in form_html)
        self.assertFalse('members-0-ORDER' in form_html)

    def test_sort_order_is_committed(self):
        class BandForm(ClusterForm):
            class Meta:
                model = Band

        form = BandForm({
            'name': "The Beatles",

            'members-TOTAL_FORMS': 0,
            'members-INITIAL_FORMS': 0,
            'members-MAX_NUM_FORMS': 1000,

            'albums-TOTAL_FORMS': 2,
            'albums-INITIAL_FORMS': 0,
            'albums-MAX_NUM_FORMS': 1000,

            'albums-0-name': 'With The Beatles',
            'albums-0-id': '',
            'albums-0-ORDER': 2,

            'albums-1-name': 'Please Please Me',
            'albums-1-id': '',
            'albums-1-ORDER': 1,
        })
        self.assertTrue(form.is_valid())
        beatles = form.save()

        self.assertEqual('Please Please Me', beatles.albums.all()[0].name)
        self.assertEqual('With The Beatles', beatles.albums.all()[1].name)
