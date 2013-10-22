# A field definition for cluster.fields.ParentalKey that is identical to ForeignKey, so that we can migrate rca/models.py cleanly

from django.db.models.fields.related import ForeignKey

try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    # south is not in use, so make add_introspection_rules a no-op
    def add_introspection_rules(*args):
        pass


class ParentalKey(ForeignKey):
    pass

add_introspection_rules([], ["^cluster\.fields\.ParentalKey"])
