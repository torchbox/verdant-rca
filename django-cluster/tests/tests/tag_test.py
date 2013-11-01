from django.test import TestCase
from taggit.models import Tag

from tests.models import Place, TaggedPlace

class TagTest(TestCase):
    def test_can_access_tags_on_unsaved_instance(self):
        mission_burrito = Place(name='Mission Burrito')
        self.assertEqual(0, mission_burrito.tags.count())

        mission_burrito.tags.add('mexican', 'burrito')
        self.assertEqual(2, mission_burrito.tags.count())
        self.assertEqual(Tag, mission_burrito.tags.all()[0].__class__)
        self.assertTrue([tag for tag in mission_burrito.tags.all() if tag.name == 'mexican'])

        mission_burrito.save()
        self.assertEqual(2, TaggedPlace.objects.filter(content_object_id=mission_burrito.id).count())
